/**
 * Утилиты для всего приложения
 */

// ==================== ФУНКЦИИ СКЛОНЕНИЯ СЛОВ ====================
function declensionWord(number, words) {
  if (!words || words.length < 3) return '';
  number = Math.abs(number) % 100;
  const remainder = number % 10;
  if (number > 10 && number < 20) return words[2];
  if (remainder > 1 && remainder < 5) return words[1];
  if (remainder === 1) return words[0];
  return words[2];
}

function formatTimer(value_seconds) {
  const total_seconds = Math.round(value_seconds);
  const minutes = Math.floor(total_seconds / 60);
  const seconds = total_seconds % 60;
  const formattedMinutes = minutes < 10 ? `0${minutes}` : minutes;
  const formattedSeconds = seconds < 10 ? `0${seconds}` : seconds;
  const wordsMinutes = ["минута", "минуты", "минут"];
  const wordsSeconds = ["секунда", "секунды", "секунд"];
  return `${formattedMinutes}\u00A0${declensionWord(minutes, wordsMinutes)}\u00A0${formattedSeconds}\u00A0${declensionWord(seconds, wordsSeconds)}`;
}


// ==================== УТИЛИТЫ ДЛЯ ФОРМ ====================
const FormUtils = {
  validateFill(listener_value) {
    if (!listener_value || listener_value.trim() === "") return null;
    return null;
  },

  updateError(inputElement, message) {
    if (!inputElement) return;
    
    let errorElement = inputElement.nextElementSibling;
    if (errorElement && errorElement.classList.contains("error-message")) {
      errorElement.remove();
    }

    if (message) {
      errorElement = document.createElement("div");
      errorElement.className = "error-message text-danger mt-1";
      errorElement.textContent = message;
      inputElement.parentNode.appendChild(errorElement);
      inputElement.classList.add("is-invalid");
    } else {
      inputElement.classList.remove("is-invalid");
    }
  },

  formatAndValidatePhone(inputElement) {
    if (!inputElement) return;
    
    let value = inputElement.value.replace(/\D/g, "");
    if (!value || value === "" || inputElement.value === "не указан") return;

    if (value.startsWith("8")) value = "7" + value.slice(1);
    if (!value.startsWith("7") && value.length > 0) value = "7" + value;
    value = value.substring(0, 11);

    let formatted = "+7";
    if (value.length > 1) formatted += " (" + value.substring(1, 4);
    if (value.length >= 4) formatted += ") " + value.substring(4, 7);
    if (value.length >= 7) formatted += "-" + value.substring(7, 9);
    if (value.length >= 9) formatted += "-" + value.substring(9, 11);

    inputElement.value = formatted;
    const isValid = value.length === 0 || value.length === 11;
    this.updateError(inputElement, isValid ? null : "Номер должен содержать 11 цифр");
  },

  attachPhoneMask(inputElement, allowEmptyText = null) {
    if (!inputElement) return;

    let isDeleting = false;
    const self = this;

    inputElement.addEventListener("keydown", function(e) {
      isDeleting = (e.key === 'Backspace' || e.key === 'Delete');
      if (allowEmptyText && this.value === allowEmptyText && isDeleting) {
        this.value = "";
        this.classList.remove("text-muted");
        e.preventDefault();
      }
    });

    inputElement.addEventListener("input", function() {
      if (allowEmptyText && this.value !== allowEmptyText && this.classList.contains("text-muted")) {
        this.classList.remove("text-muted");
        this.value = "";
      }
      
      if (!isDeleting) self.formatAndValidatePhone(this);
      
      // Обновляем поле контактного лица при изменении номера родственника
      if (this.id === 'relative_contact_phone' && window.applicationCore) {
        window.applicationCore.toggleContactPersonField();
      }
    });

    inputElement.addEventListener("blur", function() {
      const currentValue = this.value.replace(/\D/g, "");
      
      if (allowEmptyText && (!currentValue || currentValue === "")) {
        this.value = allowEmptyText;
        this.classList.add("text-muted");
        self.updateError(this, null);
      } else if (currentValue.length > 0 && currentValue.length !== 11) {
        self.updateError(this, "Номер должен содержать 11 цифр");
      } else {
        self.formatAndValidatePhone(this);
        self.updateError(this, null);
      }
      
      if (this.id === 'relative_contact_phone' && window.applicationCore) {
        window.applicationCore.toggleContactPersonField();
      }
    });

    inputElement.addEventListener("focus", function() {
      if (allowEmptyText && this.value === allowEmptyText) {
        this.value = "";
        this.classList.remove("text-muted");
      }
    });

    inputElement.addEventListener("paste", function(e) {
      e.preventDefault();
      const paste = (e.clipboardData || window.clipboardData).getData("text");
      this.value = paste;
      this.classList.remove("text-muted");
      self.formatAndValidatePhone(this);
      
      if (this.id === 'relative_contact_phone' && window.applicationCore) {
        setTimeout(() => window.applicationCore.toggleContactPersonField(), 100);
      }
    });

    // Инициализация при загрузке
    if (allowEmptyText && (!inputElement.value || inputElement.value.trim() === "" || inputElement.value === allowEmptyText)) {
      inputElement.value = allowEmptyText;
      inputElement.classList.add("text-muted");
    } else if (inputElement.value && inputElement.value !== allowEmptyText) {
      self.formatAndValidatePhone(inputElement);
    }
  },

  initializeOptionalField(field, defaultValue) {
    if (!field) return;

    field.addEventListener("blur", function() {
      if (!this.value || this.value.trim() === "") {
        this.value = defaultValue;
        this.classList.add("text-muted");
        FormUtils.updateError(this, null);
      } else {
        const error = FormUtils.validateFill(this.value);
        FormUtils.updateError(this, error);
        this.classList.remove("text-muted");
      }
    });

    field.addEventListener("focus", function() {
      if (this.value === defaultValue) {
        this.value = "";
        this.classList.remove("text-muted");
      }
    });

    field.addEventListener("input", function() {
      if (this.value === defaultValue) {
        this.value = "";
        this.classList.remove("text-muted");
      }
      const error = FormUtils.validateFill(this.value);
      FormUtils.updateError(this, error);
    });

    // Инициализация при загрузке
    if (!field.value || field.value.trim() === "" || field.value === defaultValue) {
      field.value = defaultValue;
      field.classList.add("text-muted");
    } else {
      field.classList.remove("text-muted");
    }
  }
};

// ==================== ФУНКЦИИ ДЛЯ АДМИН-ПАНЕЛИ ====================
const AdminUtils = {
  updateAdminSignature(count) {
    const signatureElement = document.getElementById("adminSignature");
    if (!signatureElement) return;

    const signatures = {
      0: "Сайт работает на магии и кофе.",
      1: "Один админ — это уже целый отдел.",
      2: "Один работает, второй думает.",
      3: "Один реальный, два виртуальных.",
      7: "Как дней в неделе. И все на выходных.",
      42: "Это ответ на главный вопрос жизни, вселенной и всего такого.",
      404: "Админ не найден.",
      911: "Срочная перезагрузка!",
      1000: "Это уже дата-центр."
    };

    signatureElement.textContent = signatures[count] || `Они как целая армия.`;
  },

  updateDoctorSignature(count) {
    const signatureElement = document.getElementById("doctorSignature");
    if (!signatureElement) return;

    const signatures = {
      0: "Лечимся народными средствами и мемами.",
      1: "Он как Доктор Хаус, только без трости.",
      7: "Как дней в неделе. И все на выходных.",
      42: "Это ответ на главный вопрос жизни, вселенной и всего такого.",
      404: "Доктор не найден.",
      911: "Срочный вызов!",
      1337: "Хацкеры медицины."
    };

    signatureElement.textContent = signatures[count] || `Они как целая больница.`;
  },

  updateDisinfectorSignature(count) {
    const signatureElement = document.getElementById("disinfectorSignature");
    if (!signatureElement) return;

    const signatures = {
      0: "Мы просто открываем окна и надеемся на лучшее.",
      1: "Он как терминатор для микробов.",
      7: "Как дней в неделе. И все в перчатках.",
      42: "Это ответ на главный вопрос жизни, вселенной и всего такого.",
      404: "Дезинфектор не найден.",
      911: "Срочная уборка!",
      1337: "Хацкеры чистоты."
    };

    signatureElement.textContent = signatures[count] || `Чистота — наше всё!`;
  },

  initAdminSignatures() {
    const adminCount = parseInt(document.getElementById("adminCount")?.textContent || 0, 10);
    const doctorCount = parseInt(document.getElementById("doctorCount")?.textContent || 0, 10);
    const disinfectorCount = parseInt(document.getElementById("disinfectorCount")?.textContent || 0, 10);

    this.updateAdminSignature(adminCount);
    this.updateDoctorSignature(doctorCount);
    this.updateDisinfectorSignature(disinfectorCount);
  }
};

// ==================== ЭКСПОРТ ГЛОБАЛЬНЫХ ПЕРЕМЕННЫХ ====================

window.declensionWord = declensionWord;
window.formatTimer = formatTimer;
window.FormUtils = FormUtils;
window.AdminUtils = AdminUtils;

// Автоматическая инициализация при загрузке
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing components');
    
    // Инициализация подписей админ-панели
    if (typeof AdminUtils !== 'undefined') {
        AdminUtils.initAdminSignatures();
    }
});