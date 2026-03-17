<template>
  <MainMenu :modelSelect="selectedItem" />
</template>

<script setup>
import { ref } from "vue";
import MainMenu from "../components/MainMenu.vue";

const selectedItem = ref("gpt-4o");
</script>

<style scoped>
/* Botón hamburguesa (oculto por defecto en pantallas grandes) */
.hamburger {
  display: none;
  /* Oculto por defecto */
  position: fixed;
  top: 10px;
  left: 10px;
  z-index: 1000;
  border: none;
  font-size: 24px;
  background: none;
  cursor: pointer;
}

.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(161, 161, 161, 0.5);
  /* Color semitransparente */
  z-index: 99;
}

/* SIDEBAR EN PANTALLAS PEQUEÑAS */
@media (max-width: 768px) {
  /* Mostrar botón hamburguesa solo en pantallas pequeñas */
  .hamburger {
    display: block;
  }

  .overlay {
    display: block;
  }

  /* Por defecto, el sidebar se oculta en pantallas pequeñas */
  .sidebar {
    display: none;
  }

  /* Cuando isSidebarVisible es true, mostramos el sidebar */
  .sidebar.sidebar-active {
    display: block;
    position: fixed;
    /* Para que aparezca sobre el contenido */
    top: 0;
    left: 0;
    width: 250px;
    height: 100%;
    background-color: #f4f4f4;
    padding: 10px;
    z-index: 999;
    /* Asegura que quede encima de otros elementos */
  }
}

/* SIDEBAR EN PANTALLAS GRANDES */
@media (min-width: 769px) {
  /* Ocultar el botón hamburguesa en pantallas grandes */
  .hamburger {
    display: none;
  }

  .overlay {
    display: none;
  }

  /* Mostrar el sidebar siempre en pantallas grandes */
  .sidebar {
    display: block;
    width: 290px;
    background-color: #f4f4f4;
    padding: 10px;
    flex-shrink: 0;
  }
}

/* Modo oscuro @media (prefers-color-scheme: dark) {
  .sidebar {

    background-color: #ff0000;

  }
}*/
</style>

<style>
.div.no-messages.chat-me {
  position: relative;
}

.div.no-messages.chat-me::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url("../assets/Bity.png");
  background-repeat: no-repeat;
  background-position: center center;
  background-size: 30%;
  opacity: 0.05;
  z-index: -1;
  pointer-events: none;
}
</style>
