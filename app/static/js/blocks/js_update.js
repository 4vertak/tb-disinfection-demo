document.addEventListener("DOMContentLoaded", function () {
  const changePasswordCheckbox = document.getElementById("change_password");
  const passwordFields = document.getElementById("password_fields");
  const currentPasswordField = document.querySelector(".current-password-field");
  const currentPasswordInput = document.getElementById("current_password");
  const newPasswordInput = document.getElementById("new_password");
  const confirmNewPasswordInput = document.getElementById("confirm_new_password");

  if (changePasswordCheckbox && passwordFields) {
    // Функция показа/скрытия полей пароля
    function togglePasswordFields() {
      const isChecked = changePasswordCheckbox.checked;
      
      if (isChecked) {
        passwordFields.style.display = "block";
      } else {
        passwordFields.style.display = "none";
      }

      // Определяем видимость поля текущего пароля
      const isCurrentPasswordHidden = !currentPasswordField || 
                                       currentPasswordField.style.display === "none" ||
                                       currentPasswordField.classList.contains("d-none");

      // Устанавливаем обязательность полей
      if (currentPasswordInput) {
        currentPasswordInput.required = isChecked && !isCurrentPasswordHidden;
      }
      if (newPasswordInput) {
        newPasswordInput.required = isChecked;
      }
      if (confirmNewPasswordInput) {
        confirmNewPasswordInput.required = isChecked;
      }
    }

    // Слушаем изменения
    changePasswordCheckbox.addEventListener("change", togglePasswordFields);

    // Инициализация при загрузке
    togglePasswordFields();
  }
});
