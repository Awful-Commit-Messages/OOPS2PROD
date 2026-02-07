const logger_button = document.getElementById("logger_button");
let logger_button_toggle = false;

logger_button.addEventListener("click", function () {
  logger_button_toggle = !logger_button_toggle;

  logger_button.innerText = logger_button_toggle
    ? "Logger (on)"
    : "Logger (off)";
});
