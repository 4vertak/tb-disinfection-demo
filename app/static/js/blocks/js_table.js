

$(document).ready(function () {
  $("#myTableChanges").DataTable({
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.2.0/i18n/ru.json",
    },
    order: {
      idx: 1,
      dir: "desc",
    },
  });
});

$(document).ready(function () {
  // Инициализация DataTable
  var table = $("#myTableAdmins").DataTable({
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.2.0/i18n/ru.json",
    },
    order: {
      idx: 1,
      dir: "desc",
    },
    // Добавляем класс для колонки с типом пользователя
    // Предполагаем, что тип пользователя находится в 4-й колонке (индекс 3)
    columnDefs: [{ targets: 3, className: "user-type" }],
  });

  // Обработчик клика по фильтрам
  $(".filter-link").on("click", function (e) {
    e.preventDefault();

    var filterType = $(this).data("filter");

    // Сбрасываем все фильтры
    table.search("").columns().search("").draw();

    // Применяем фильтр по типу пользователя
    if (filterType) {
      if (filterType === "all") {
        table.search("").draw();
      } else {
        // Фильтруем по колонке с типом пользователя (индекс 3)
        table.column(3).search(filterType).draw();
      }
    }
  });

  // Опционально: выделяем активный фильтр
  $(".filter-link").on("click", function () {
    $(".filter-link").removeClass("active-filter");
    $(this).addClass("active-filter");
  });
});

$(document).ready(function () {
  $("#myTableApplications").DataTable({
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.2.0/i18n/ru.json",
    },
    order: {
      idx: 1,
      dir: "desc",
    },
  });
});



$(document).ready(function () {
  $("#myTableDisinfectors").DataTable({
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.2.0/i18n/ru.json",
    },
    order: {
      idx: 1,
      dir: "desc",
    },
  });
});

$(document).ready(function () {
  $("#myTableDoctors").DataTable({
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.2.0/i18n/ru.json",
    },
    order: {
      idx: 1,
    },
  });
});

