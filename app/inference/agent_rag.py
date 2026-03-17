## _______________________________________________________________________________________
## En este archivo se define el agente RAG (Retrieval-Augmented Generation) utilizando LangGraph.
## El agente gestiona el flujo de conversación, incluyendo la interacción con el LLM,
## la ejecución de herramientas (búsqueda en índices) y el manejo de la memoria por sesión.
## _______________________________________________________________________________________

# -----------------------------------------------------------------------------------------
# region             Librerías
# -----------------------------------------------------------------------------------------

import re
import operator
from typing import Annotated, Dict
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END

from app.integrations.azure_openai_provider import openai_provider
from app.prompts.agent_prompt import prompt_react_agentic
from app.tools.search_tool import search
from app.core.utils import generate_id

# State and Tool definitions
from app.core import context
from app.tools.search_userdocs_tool import search_userdocs


# -----------------------------------------------------------------------------------------
# region             Memoria volátil por sesión
# -----------------------------------------------------------------------------------------

from typing import Dict, List
from langchain_core.messages import AnyMessage

session_histories: Dict[str, List[AnyMessage]] = {}
MAX_HISTORY_MESSAGES = 20   # Ajustable según necesidad

def clear_session_history(session_id: str):
    """Elimina el historial de una sesión de la memoria volátil."""
    if session_id in session_histories:
        del session_histories[session_id]
        print(f"🧹 Historial eliminado para sesión: {session_id}")



# -----------------------------------------------------------------------------------------
# region             Herramientas y definición del estado del grafo
# -----------------------------------------------------------------------------------------

tools = [search, search_userdocs]

# Graph state definition
class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    citations: list[Dict]


# -----------------------------------------------------------------------------------------
# region             Clase Agent (implementación del agente con LangGraph)
# -----------------------------------------------------------------------------------------

class Agent:
    """
    Agente RAG que utiliza LangGraph para orquestar la conversación.
    Gestiona la interacción con el LLM, la ejecución de herramientas y el formateo de respuestas.
    """

    def __init__(self, model, tools, system=''):
        """
        Inicializa el agente, configura el grafo de estados y enlaza las herramientas al modelo.

        Args:
            model: Modelo de lenguaje (AzureChatOpenAI).
            tools: Lista de herramientas disponibles.
            system: Prompt de sistema (instrucciones para el agente).
        """
        self.system = system

        # Initialize state graph
        graph = StateGraph(GraphState)

        # Add nodes
        graph.add_node('llm', self._action_llm)
        graph.add_node('action', self._action_node)
        graph.add_node('response', self._action_response)

        # Conditional routing from LLM
        graph.add_conditional_edges(
            'llm',
            self._router,
            { True: 'action', False: 'response' }
        )

        # Define flow
        graph.add_edge(START, 'llm')
        graph.add_edge('action', 'llm')
        graph.add_edge('response', END)

        # Compile graph
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}

        # Bind tools to model
        self.model = model.bind_tools(tools)

    def _router(self, state: GraphState):
        """
        Enrutador: decide si se debe ejecutar una herramienta (True) o responder directamente (False).
        """
        if isinstance(state, list):
            ai_message = state[-1]
        elif messages := state.get('messages', []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in state: {state}")

        # Comprueba si el último mensaje del LLM contiene llamadas a herramientas
        if hasattr(ai_message, 'tool_calls') and len(ai_message.tool_calls) > 0:
            return True
        return False

    async def _action_llm(self, state: GraphState):
        """
        Nodo de interacción con el LLM. Construye el prompt con el historial y ejecuta el modelo.
        """
        messages = state['messages']
        if self.system:
            # Build prompt with system message and history
            prompt_template = ChatPromptTemplate([
                ("system", self.system),
                MessagesPlaceholder("messages")
            ])
            messages = prompt_template.invoke({
                "messages": messages,
            }).messages

        # Invoke LLM
        message = await self.model.ainvoke(messages)
        return {'messages': [message]}

    async def _action_node(self, state: GraphState):
        """
        Nodo de acción: ejecuta las herramientas solicitadas por el LLM y acumula resultados y citas.
        """
        tool_calls = state['messages'][-1].tool_calls
        results = []
        all_citations = []  # Para acumular citas de todas las herramientas

        for t in tool_calls:
            print(f'🔧 Llamando a herramienta: {t["name"]} con args: {t["args"]}')

            if t['name'] not in self.tools:
                print(f"❌ Herramienta no encontrada: {t['name']}")
                result_content = "bad tool name, retry"
                citations = []
            else:
                try:
                    # Invoca la herramienta y obtiene el resultado
                    print(f"✅ Invocando herramienta {t['name']}...")
                    raw_result = await self.tools[t['name']].ainvoke(t['args'])
                    print(f"✅ Resultado recibido de {t['name']}")
                    print(f"   Tipo de resultado: {type(raw_result)}")

                    if isinstance(raw_result, dict):
                        result_content = raw_result.get("results_str", "")
                        citations = raw_result.get("results", [])
                        print(f"📊 Citas encontradas: {len(citations)}")
                        print(f"   Result string: {result_content[:200]}...")

                        # Acumular citas
                        all_citations.extend(citations)
                    else:
                        result_content = str(raw_result)
                        citations = []
                        print(f"📝 Resultado como string: {result_content[:200]}...")

                except Exception as e:
                    print(f"❌ Error en herramienta {t['name']}: {e}")
                    import traceback
                    traceback.print_exc()
                    result_content = f"Error en herramienta: {str(e)}"
                    citations = []

            # Agrega el resultado de la herramienta a la lista de mensajes
            results.append(ToolMessage(
                tool_call_id=t['id'],
                name=t['name'],
                content=result_content
            ))

        print('↩️ Regresando al modelo...')
        return { 'messages': results, 'citations': all_citations }

    async def _action_response(self, state: GraphState):
        """
        Nodo de respuesta: formatea la salida final, extrae las citas referenciadas y limpia el texto.
        """
        last_message = state['messages'][-1]
        model_output = last_message.content
        citations = state.get('citations', [])

        # Regex flexible para encontrar la sección de referencias
        # Soporta: **Referencias:**, Referencias:, ## Referencias, etc.
        ref_regex = r"(?:\*\*|##|\n|^)\s*Referencias\s*(?:\*\*|:)?\s*:?\s*(.*)"
        ref_match = re.search(ref_regex, model_output, re.IGNORECASE | re.DOTALL)

        new_citations = []

        if ref_match:
            refs_text = ref_match.group(1).strip()

            # 1. Intenta extraer índices entre corchetes [1], [2]
            indexes = re.findall(r"\[(\d+)\]", refs_text)

            # 2. Si no hay corchetes, busca números planos separados por comas/espacios
            if not indexes:
                plain_numbers = re.findall(r"\b(\d+)\b", refs_text)
                if plain_numbers:
                    print("Warning: Model used plain numbers instead of [N] format")
                    indexes = plain_numbers

            # 3. Fallback: Si la sección existe pero está vacía o mal formada (ej: ", ,")
            # o si no se encontraron números, usamos todas las citas disponibles.
            if not indexes:
                # Si el texto es corto o no tiene caracteres alfanuméricos (solo puntuación)
                if len(refs_text) < 20 or not any(c.isalnum() for c in refs_text):
                    print("Warning: Model provided empty/malformed reference section, using all citations")
                    indexes = [str(i+1) for i in range(len(citations))]

            unique_indexes = sorted(set(int(i) for i in indexes))

            for i in unique_indexes:
                if 0 < i <= len(citations):
                    citation_data = citations[i-1]
                    # Map fields to the requested structure
                    page_val = citation_data.get("page_number")
                    page_start = citation_data.get("page_start")
                    page_end = citation_data.get("page_end")

                    if page_start is not None and page_end is not None:
                        if page_start == page_end:
                            page_display = str(page_start)
                        else:
                            page_display = f"{page_start}-{page_end}"
                    else:
                        page_display = str(page_val) if page_val is not None else None

                    formatted_citation = {
                        "index": i,
                        "page": page_display,
                        "section": citation_data.get("section"),
                        "chunk": citation_data.get("chunk_id"),
                        "snippet": citation_data.get("snippet"),
                        "url": citation_data.get("blob_url"),
                        "filename": citation_data.get("filename")
                    }
                    new_citations.append(formatted_citation)

        # Quita la sección de referencias del texto usando el mismo regex flexible
        answer = re.sub(ref_regex, "", model_output, flags=re.IGNORECASE | re.DOTALL).strip()
        # Keep inline [N] citations in the answer text - they'll be rendered as hoverable badges by frontend

        formated_msg = AIMessage(
            content=answer,
            usage_metadata=last_message.usage_metadata
        )
        return { 'messages': [formated_msg], 'citations': new_citations }



# -----------------------------------------------------------------------------------------
# region             Instancia global del agente
# -----------------------------------------------------------------------------------------

agent_rag = Agent(
    model=openai_provider.model_ai,
    tools=tools,
    system=prompt_react_agentic,
)



# -----------------------------------------------------------------------------------------
# region             Función principal run_agent
# -----------------------------------------------------------------------------------------

async def run_agent(query: str, session_id: str, user_id: str = None) -> Dict:
    """
    Ejecuta el agente con la query del usuario.
    - Recupera historial desde session_histories.
    - Añade el nuevo mensaje.
    - Ejecuta el agente.
    - Guarda el historial actualizado.

    Args:
        query: Mensaje del usuario.
        session_id: Identificador de la sesión.
        user_id: Identificador del usuario (opcional, para contexto).

    Returns:
        Diccionario con message_id, texto de respuesta y lista de citas.
    """
    print(f"🚀 Iniciando run_agent")
    print(f"   Query: {query}")
    print(f"   Session: {session_id}")
    print(f"   User: {user_id}")

    # Establece el contexto para las herramientas
    user_token = None
    session_token = None
    if user_id:
        user_token, session_token = context.set_rag_context(user_id, session_id)
        print(f"   Contexto establecido: user={user_id}, session={session_id}")

    try:
        # 1. Cargar historial desde memoria volátil
        history = session_histories.get(session_id, [])
        # Limitar tamaño para no sobrecargar el contexto
        if len(history) > MAX_HISTORY_MESSAGES:
            history = history[-MAX_HISTORY_MESSAGES:]
        print(f"📚 Historial recuperado para sesión {session_id}: {len(history)} mensajes")

        # 2. Añadir el nuevo mensaje del usuario
        history.append(HumanMessage(content=query))
        print(f"   Total mensajes en historial (con nuevo): {len(history)}")

        # 3. Ejecutar el agente con el historial completo
        print("🤖 Ejecutando agente LangGraph...")
        state = await agent_rag.graph.ainvoke({ 'messages': history })
        print("✅ Agente ejecutado")

        # 4. Obtener el último mensaje (respuesta) y las citas
        ai_message = state['messages'][-1]
        ai_response_text = ai_message.content
        citations_list = state.get('citations', [])   # Sigue siendo útil para la respuesta inmediata

        # 5. Actualizar el historial en memoria con TODOS los mensajes generados
        #    Esto incluye mensajes de herramienta, pensamientos intermedios, etc.
        updated_history = state['messages']
        if len(updated_history) > MAX_HISTORY_MESSAGES:
            updated_history = updated_history[-MAX_HISTORY_MESSAGES:]
        session_histories[session_id] = updated_history
        print(f"💾 Historial actualizado para sesión {session_id}: {len(updated_history)} mensajes")

        # 6. Generar ID del mensaje (sin Cosmos DB)
        message_id = f"msg-{generate_id()}"

        # 7. Retornar el formato esperado por el endpoint
        return {
            "message_id": message_id,
            "text": ai_response_text,
            "citations": citations_list
        }
    except Exception as e:
        print(f"❌ Error en run_agent: {e}")
        import traceback
        traceback.print_exc()
        return {
            "message_id": f"error-{generate_id()}",
            "text": f"Error procesando la solicitud: {str(e)}",
            "citations": []
        }
    finally:
        # Reset context
        if user_token and session_token:
            context.reset_rag_context(user_token, session_token)

