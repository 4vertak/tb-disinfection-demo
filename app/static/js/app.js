// Скрипт для отображения сообщений в блоке flash-messages
$(document).ready(function () {
  var hideTime = 3000; // 3000 мс = 3 секунды

  setTimeout(function () {
    $("#flash-messages").fadeOut("slow");
  }, hideTime);
});
