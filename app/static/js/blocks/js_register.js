// Показываем поле выбора участка только при выборе типа пользователя "Врач"
function toggleAreaField() {
    var userTypeSelect = document.getElementById('user_type');
    var areaField = document.getElementById('areaField');
    
    if (!userTypeSelect || !areaField) {
        return;
    }
    
    if (userTypeSelect.value === 'doctor') {
        areaField.style.display = 'block';
    } else {
        areaField.style.display = 'none';
    }
}

document.addEventListener("DOMContentLoaded", function () {
    var userTypeSelect = document.getElementById('user_type');
    
    if (userTypeSelect) {
        userTypeSelect.addEventListener('change', toggleAreaField);
    }
    
    // Инициализация при загрузке
    toggleAreaField();
});
