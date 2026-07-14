/**
 * Основная логика приложения для работы с заявками
 */

const ApplicationCore = {
  // ==================== СВОЙСТВА ДЛЯ ПРЕЛОАДЕРА ====================
  loadingMessages: [
    "Проверяем вашу заявку...",
    "Отправляем данные в систему...",
    "Обрабатываем информацию...",
    "Проверяем эпидемиологические данные...",
    "Формируем документы дезинфекции...",
    "Завершаем обработку...",
    "Почти готово..."
  ],

  disinfectFacts: [
    "Дезинфекция уничтожает 99.9% патогенных микроорганизмов",
    "Обработка помещения занимает от 30 минут до 2 часов",
    "Оптимальная температура для дезинфекции - 20-25°C",
    "Современные дезинфектанты безопасны для людей и животных",
    "Эффективность дезинфекции контролируется лабораторно",
    "После обработки рекомендуется проветривание 1-2 часа",
    "Все работы проводятся сертифицированными специалистами"
  ],

  // Флаг для отслеживания инициализации
  _initialized: false,

  // ==================== ОСНОВНЫЕ МЕТОДЫ ====================
  init() {
    // Защита от двойной инициализации
    if (this._initialized) {
      console.log('ApplicationCore уже инициализирован, пропускаем');
      return;
    }
    
    console.log('Инициализация ApplicationCore');
    this._initialized = true;
    
    this.initApplicationForms();
    this.initDashboardComponents();
    this.initTextUpdaters();
    this.initFormSubmissionHandlers();
  },

   // ==================== МЕТОДЫ ПРЕЛОАДЕРА ====================
  initFormSubmissionHandlers() {
    this.initFormSubmissionHandler('application-form', 'submit-btn', 'submit-text', 'submit-loading', 'typing-text');
  },

  initFormSubmissionHandler(formId, btnId, textId, loadingId, typingId) {
    const form = document.getElementById(formId);
    const submitBtn = document.getElementById(btnId);
    const submitText = document.getElementById(textId);
    const submitLoading = document.getElementById(loadingId);
    
    if (form && submitBtn) {
      form.addEventListener('submit', (e) => {
        // Проверяем, не отправляется ли уже форма
        if (form.classList.contains('form-submitting')) {
          e.preventDefault();
          return;
        }
        
        // Блокируем форму и показываем индикатор загрузки
        this.startFormLoading(form, submitBtn, submitText, submitLoading, typingId);
        
        // Дополнительная защита: блокируем повторную отправку
        setTimeout(() => {
          submitBtn.disabled = true;
        }, 100);
      });
      
      // Обработчик для разблокировки формы при возврате на страницу
      window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
          this.resetFormState(form, submitBtn, submitText, submitLoading);
        }
      });
    }
  },

  startFormLoading(form, submitBtn, submitText, submitLoading, typingId) {
    form.classList.add('form-submitting');
    submitBtn.disabled = true;
    submitBtn.classList.add('btn-loading');
    
    if (submitText) submitText.classList.add('d-none');
    if (submitLoading) submitLoading.classList.remove('d-none');
    
    // Запускаем анимацию с эффектом печатания
    this.startLoadingAnimation(typingId);
  },

  resetFormState(form, submitBtn, submitText, submitLoading) {
    if (form && submitBtn) {
      form.classList.remove('form-submitting');
      submitBtn.disabled = false;
      submitBtn.classList.remove('btn-loading');
      if (submitText) submitText.classList.remove('d-none');
      if (submitLoading) submitLoading.classList.add('d-none');
    }
  },

  // Функция для эффекта печатания текста
  typeWriter(element, text, speed = 50, callback = null) {
    let i = 0;
    element.innerHTML = ''; // Очищаем предыдущий текст
    
    function type() {
      if (i < text.length) {
        element.innerHTML += text.charAt(i);
        i++;
        setTimeout(type, speed);
      } else if (callback) {
        // Добавляем мигающий курсор после текста
        element.innerHTML += '<span class="typing-cursor"></span>';
        setTimeout(callback, 1500);
      }
    }
    type();
  },

  // Функция для запуска анимации загрузки
  startLoadingAnimation(typingElementId) {
    const typingElement = document.getElementById(typingElementId);
    if (!typingElement) return;
    
    let messageIndex = 0;
    let factIndex = 0;
    const self = this;
    
    function showNextMessage() {
      if (messageIndex < self.loadingMessages.length) {
        // Показываем сообщение о ходе обработки
        self.typeWriter(typingElement, self.loadingMessages[messageIndex], 40, () => {
          messageIndex++;
          // После 3-го сообщения начинаем показывать факты
          if (messageIndex >= 3 && factIndex < self.disinfectFacts.length) {
            showFact();
          } else {
            setTimeout(showNextMessage, 500);
          }
        });
      } else {
        // Циклически повторяем сообщения, если загрузка долгая
        messageIndex = 3; // Начинаем с позиции показа фактов
        showFact();
      }
    }
    
    function showFact() {
      if (factIndex < self.disinfectFacts.length) {
        self.typeWriter(typingElement, self.disinfectFacts[factIndex], 30, () => {
          factIndex++;
          // Чередуем факты и сообщения о прогрессе
          if (messageIndex < self.loadingMessages.length) {
            setTimeout(showNextMessage, 800);
          } else {
            setTimeout(showFact, 1000);
          }
        });
      } else {
        // Начинаем цикл заново
        factIndex = 0;
        messageIndex = 3;
        setTimeout(showFact, 500);
      }
    }
    
    showNextMessage();
  },

  // ==================== ИНИЦИАЛИЗАЦИЯ ФОРМ ====================
  initApplicationForms() {
    this.toggleReasonField();
    this.initAddressAutocomplete();
    
    // Сначала парсим контактные данные ДО применения масок
    this.initContactPersonLogic();
    
    // Затем применяем маски телефонов
    this.initPhoneMasks();
    
    this.initOptionalFields();
    this.initDoctorAutocomplete();
    this.initDisinfectorAutocomplete();
    this.initDiagnosisSelect();
    this.initAddEntryForm();
    // Валидация перед отправкой формы
    this.initFormValidation();
  },

  // ==================== ЛОГИКА ДЛЯ ФОРМЫ ДОБАВЛЕНИЯ ДАННЫХ ====================
  initAddEntryForm() {
    const areaSizeInput = document.getElementById("area_size");
    const rejectionCheckbox = document.getElementById("rejection");
    
    if (areaSizeInput) {
      areaSizeInput.addEventListener("input", function() {
        this.value = this.value.replace(",", ".");
        const areaSize = parseFloat(this.value) || 0;
        const volumeSize = areaSize * 3.0;
        const sprayingTime = volumeSize * 3.6;
        const formattedSprayingTime = formatTimer(sprayingTime);

        const volumeSizeInput = document.getElementById("volume_size");
        const sprayingTimeInput = document.getElementById("spraying_time");
        
        if (volumeSizeInput) volumeSizeInput.value = volumeSize.toFixed(2);
        if (sprayingTimeInput) sprayingTimeInput.value = formattedSprayingTime;
      });
    }

    if (rejectionCheckbox) {
      rejectionCheckbox.addEventListener("change", () => this.toggleRejectionFields());
      this.toggleRejectionFields();
    }
  },

  toggleRejectionFields() {
    const rejectionCheckbox = document.getElementById("rejection");
    const reasonField = document.getElementById("reasonField");
    const reasonInput = document.getElementById("rejection_reason");
    const areaField = document.getElementById("areaField");
    const volumeField = document.getElementById("volumeField");
    const sprayingField = document.getElementById("sprayingField");

    if (!rejectionCheckbox || !reasonField) return;

    const isChecked = rejectionCheckbox.checked;
    
    if (reasonField) reasonField.style.display = isChecked ? "block" : "none";
    if (areaField) areaField.style.display = isChecked ? "none" : "block";
    if (volumeField) volumeField.style.display = isChecked ? "none" : "block";
    if (sprayingField) sprayingField.style.display = isChecked ? "none" : "block";

    if (reasonInput) {
      if (isChecked && (!reasonInput.value || reasonInput.value.trim() === "")) {
        reasonInput.value = "Отказ";
        reasonInput.classList.add("text-muted");
      } else if (!isChecked) {
        reasonInput.value = "";
        reasonInput.classList.remove("text-muted");
      }
    }
  },

  // ==================== ЛОГИКА АДРЕСНОГО АВТОДОПОЛНЕНИЯ ====================
  initAddressAutocomplete() {
    const addressInput = document.getElementById("address");
    const suggestionsBox = document.getElementById("address-suggestions");
    
    if (!addressInput || !suggestionsBox) return;

    let currentIndex = -1;

    // Установка города по умолчанию только если поле пустое
    if (!addressInput.value.trim()) {
      addressInput.value = "г Якутск";
      // Добавляем флаг, что это значение по умолчанию
      addressInput.dataset.isDefault = "true";
      addressInput.dataset.wasValidated = "false";
    }

    // Отслеживаем начало ввода пользователем
    addressInput.addEventListener("focus", () => {
      // При фокусе на поле, если это значение по умолчанию, очищаем его
      if (addressInput.dataset.isDefault === "true") {
        addressInput.value = "";
        addressInput.dataset.isDefault = "false";
      }
      addressInput.dataset.wasFocused = "true";
    });

    // Валидация адреса при изменении (только после начала ввода)
    addressInput.addEventListener("input", function() {
      // Если пользователь начал ввод, убираем флаг значения по умолчанию
      if (this.dataset.isDefault === "true") {
        this.dataset.isDefault = "false";
      }
      
      const query = addressInput.value.trim();
      
      // Показываем подсказки только если запрос длиннее 2 символов
      if (query.length < 3) {
        suggestionsBox.innerHTML = "";
        return;
      }

      fetch("/api/suggest/address", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      })
      .then(res => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then(data => {
        suggestionsBox.innerHTML = "";
        currentIndex = -1;
        
        if (data.suggestions && data.suggestions.length > 0) {
          data.suggestions.forEach((suggestion, idx) => {
            const item = document.createElement("div");
            item.classList.add("list-group-item", "list-group-item-action");
            item.textContent = suggestion.value;

            item.addEventListener("mouseenter", () => {
              this.clearActiveSuggestions(suggestionsBox);
              currentIndex = idx;
              item.classList.add("active");
            });

            item.addEventListener("click", () => {
              addressInput.value = suggestion.value;
              addressInput.dataset.isDefault = "false"; // Снимаем флаг при выборе из подсказок
              addressInput.dataset.wasValidated = "true"; // Помечаем, что поле было валидировано
              suggestionsBox.innerHTML = "";
              // Валидация после выбора адреса
              ApplicationCore.validateAddressField(true);
            });

            suggestionsBox.appendChild(item);
          });
        }
      })
      .catch(err => console.error('Error fetching address suggestions:', err));
    });

    // Валидация адреса при потере фокуса (только если поле было изменено)
    addressInput.addEventListener("blur", () => {
      // Валидируем только если поле было в фокусе или изменено
      if (addressInput.dataset.wasFocused === "true" || addressInput.value !== "г Якутск") {
        ApplicationCore.validateAddressField(true);
      }
    });

    addressInput.addEventListener("keydown", function(e) {
      const items = suggestionsBox.querySelectorAll(".list-group-item");
      if (!items.length) return;

      if (e.key === "ArrowDown") {
        currentIndex = (currentIndex + 1) % items.length;
        ApplicationCore.updateActiveSuggestion(items, currentIndex);
        e.preventDefault();
      } else if (e.key === "ArrowUp") {
        currentIndex = (currentIndex - 1 + items.length) % items.length;
        ApplicationCore.updateActiveSuggestion(items, currentIndex);
        e.preventDefault();
      } else if (e.key === "Enter") {
        if (currentIndex >= 0 && items[currentIndex]) {
          addressInput.value = items[currentIndex].textContent;
          addressInput.dataset.isDefault = "false"; // Снимаем флаг при выборе через Enter
          addressInput.dataset.wasValidated = "true"; // Помечаем, что поле было валидировано
          suggestionsBox.innerHTML = "";
          ApplicationCore.validateAddressField(true);
          e.preventDefault();
        } else {
          // Если просто нажали Enter без выбора из списка - валидируем только если поле было изменено
          if (addressInput.dataset.wasFocused === "true" || addressInput.value !== "г Якутск") {
            ApplicationCore.validateAddressField(true);
          }
        }
      } else if (e.key === "Escape") {
        suggestionsBox.innerHTML = "";
      }
    });

    document.addEventListener("click", function(e) {
      if (e.target !== addressInput && !suggestionsBox.contains(e.target)) {
        suggestionsBox.innerHTML = "";
      }
    });
  },

  // Валидация поля адреса (только при force=true или если поле уже было валидировано)
  validateAddressField(force = false) {
    const addressInput = document.getElementById("address");
    if (!addressInput) return true;

    const addressValue = addressInput.value.trim();
    
    // Если валидация не принудительная и поле еще не было в фокусе/изменено, пропускаем
    if (!force && addressInput.dataset.wasValidated !== "true" && addressValue === "г Якутск") {
      return true;
    }
    
    // Помечаем, что поле прошло валидацию
    addressInput.dataset.wasValidated = "true";
    
    // Очистка предыдущих состояний валидации
    addressInput.classList.remove('is-valid', 'is-invalid');
    this.clearValidationFeedback(addressInput);
    
    // Если поле пустое
    if (addressValue === '') {
      this.showValidationError(addressInput, 'Адрес обязателен для заполнения');
      return false;
    }
    
    // Проверка на адрес по умолчанию
    const isDefaultAddress = addressInput.dataset.isDefault === "true" || 
                           addressValue === "г Якутск" || 
                           addressValue === "г Якутск,";
    
    if (isDefaultAddress) {
      this.showValidationError(addressInput, 'Пожалуйста, укажите полный адрес (улица, дом, квартира)');
      return false;
    }
    
    // Проверка на минимальную длину адреса (должен содержать больше чем просто город)
    if (addressValue.length < 10) {
      this.showValidationError(addressInput, 'Адрес должен содержать улицу и номер дома');
      return false;
    }
    
    // Проверка на наличие номера дома (содержит цифры)
    const hasHouseNumber = /\d/.test(addressValue);
    if (!hasHouseNumber) {
      this.showValidationError(addressInput, 'Адрес должен содержать номер дома');
      return false;
    }
    
    this.showValidationSuccess(addressInput, '✓ Адрес корректен');
    return true;
  },

  clearActiveSuggestions(suggestionsBox) {
    if (!suggestionsBox) return;
    suggestionsBox.querySelectorAll(".list-group-item")
      .forEach(item => item.classList.remove("active"));
  },

  updateActiveSuggestion(items, currentIndex) {
    items.forEach(item => item.classList.remove("active"));
    if (currentIndex >= 0 && items[currentIndex]) {
      items[currentIndex].classList.add("active");
    }
  },

  // ==================== ЛОГИКА ТЕЛЕФОНОВ И КОНТАКТНЫХ ЛИЦ ====================
  initPhoneMasks() {
    // Применяем маски только после парсинга контактных данных
    FormUtils.attachPhoneMask(document.getElementById("contact_phone"));
    
    // Для relative_contact_phone применяем маску только к телефонной части
    const relativePhoneInput = document.getElementById("relative_contact_phone");
    if (relativePhoneInput) {
      // Получаем текущее значение (уже должно быть распарсено)
      const currentValue = relativePhoneInput.value;
      
      // Если значение содержит только телефон (без &), применяем маску
      if (!currentValue.includes('&')) {
        FormUtils.attachPhoneMask(relativePhoneInput, "не указан");
      } else {
        // Если значение содержит &, разделяем и применяем маску только к телефонной части
        const phonePart = currentValue.split('&')[0].trim();
        relativePhoneInput.value = phonePart;
        FormUtils.attachPhoneMask(relativePhoneInput, "не указан");
      }
    }
    
    // Добавляем валидацию для предотвращения ввода текста
    this.initPhoneValidation();
  },

  // Инициализация валидации телефонов
  initPhoneValidation() {
    const contactPhone = document.getElementById("contact_phone");
    const relativePhone = document.getElementById("relative_contact_phone");
    
    if (contactPhone) {
      contactPhone.addEventListener('input', (e) => this.validatePhoneInput(e.target));
      contactPhone.addEventListener('blur', (e) => this.validatePhoneField(e.target));
      contactPhone.addEventListener('paste', (e) => this.handlePhonePaste(e));
    }
    
    if (relativePhone) {
      relativePhone.addEventListener('input', (e) => this.validatePhoneInput(e.target));
      relativePhone.addEventListener('blur', (e) => this.validatePhoneField(e.target));
      relativePhone.addEventListener('paste', (e) => this.handlePhonePaste(e));
    }
  },

  // Валидация ввода телефона - предотвращение ввода текста
  validatePhoneInput(phoneInput) {
    if (!phoneInput) return;
    
    // Сохраняем позицию курсора
    const cursorPosition = phoneInput.selectionStart;
    
    // Удаляем все символы, кроме цифр, плюса, скобок, пробелов и дефисов
    let value = phoneInput.value;
    const originalLength = value.length;
    
    // Разрешаем только: цифры, +, (, ), -, пробелы
    value = value.replace(/[^\d+()\-\s]/g, '');
    
    // Если значение изменилось, обновляем поле
    if (value.length !== originalLength) {
      phoneInput.value = value;
      
      // Восстанавливаем позицию курсора с учетом удаленных символов
      const deletedChars = originalLength - value.length;
      const newCursorPosition = Math.max(0, cursorPosition - deletedChars);
      phoneInput.setSelectionRange(newCursorPosition, newCursorPosition);
    }
    
    // Очищаем сообщения об ошибках при вводе
    phoneInput.classList.remove('is-invalid');
    this.clearValidationFeedback(phoneInput);
  },

  // Обработка вставки текста в поле телефона
  handlePhonePaste(e) {
    e.preventDefault();
    
    // Получаем текст из буфера обмена
    const pastedText = (e.clipboardData || window.clipboardData).getData('text');
    
    // Очищаем от нечисловых символов (оставляем только цифры)
    const cleanedText = pastedText.replace(/\D/g, '');
    
    // Вставляем очищенный текст
    const start = e.target.selectionStart;
    const end = e.target.selectionEnd;
    const value = e.target.value;
    
    e.target.value = value.substring(0, start) + cleanedText + value.substring(end);
    
    // Устанавливаем курсор после вставленного текста
    const newCursorPosition = start + cleanedText.length;
    e.target.setSelectionRange(newCursorPosition, newCursorPosition);
    
    // Запускаем валидацию
    this.validatePhoneInput(e.target);
  },

  // Валидация поля телефона при потере фокуса
  validatePhoneField(phoneInput) {
    if (!phoneInput) return true;

    const phoneValue = phoneInput.value;
    const isValid = this.validatePhone(phoneValue);

    // Очистка предыдущих состояний валидации
    phoneInput.classList.remove('is-valid', 'is-invalid');
    this.clearValidationFeedback(phoneInput);

    if (!isValid && phoneValue && phoneValue !== 'не указан' && phoneValue !== '+7 (   )    -  -') {
      this.showValidationError(phoneInput, 'Введите корректный номер телефона');
      return false;
    } else if (isValid && phoneValue && phoneValue !== 'не указан' && phoneValue !== '+7 (   )    -  -') {
      this.showValidationSuccess(phoneInput, '✓ Номер корректен');
      return true;
    }
    
    return true; // Для пустых или специальных значений считаем валидным
  },

  // Существующий метод validatePhone (оставляем без изменений)
  validatePhone(phoneValue) {
    if (!phoneValue || phoneValue === 'не указан' || phoneValue === '+7 (   )    -  -') {
      return false;
    }
    const digits = phoneValue.replace(/\D/g, '');
    return digits.length >= 10;
  },

  initOptionalFields() {
    FormUtils.initializeOptionalField(document.getElementById("workplace"), "не работает");
    FormUtils.initializeOptionalField(document.getElementById("position"), "не работает");
  },

  initContactPersonLogic() {
    // Сначала парсим данные при загрузке
    this.parseContactDataOnLoad();
    
    // Затем инициализируем логику отображения
    this.toggleContactPersonField();

    const relativePhone = document.getElementById('relative_contact_phone');
    const contactPerson = document.getElementById('contact_person');
    const form = document.querySelector('form');

    if (relativePhone) {
      relativePhone.addEventListener('input', () => setTimeout(() => this.toggleContactPersonField(), 50));
      relativePhone.addEventListener('blur', () => this.toggleContactPersonField());
      relativePhone.addEventListener('change', () => this.toggleContactPersonField());
    }

    if (contactPerson) {
      contactPerson.addEventListener('input', () => this.toggleContactPersonField());
      contactPerson.addEventListener('blur', () => this.toggleContactPersonField());
    }

    if (form) {
      form.addEventListener('submit', (e) => {
        this.combineContactDataBeforeSubmit();
        // Добавляем небольшую задержку для гарантии обработки
        setTimeout(() => {}, 100);
      });
    }
  },

  toggleContactPersonField() {
    const relativePhone = document.getElementById('relative_contact_phone');
    const contactPersonField = document.getElementById('contact_person_field');
    const contactPersonInput = document.getElementById('contact_person');
    
    if (!relativePhone || !contactPersonField) return;
    
    const currentPhoneValue = relativePhone.value.trim();
    const hasValidPhone = this.validatePhone(currentPhoneValue);
    const hasContactPerson = contactPersonInput && contactPersonInput.value.trim() !== '';
    
    // Показываем поле контактного лица если есть валидный телефон ИЛИ есть контактное лицо
    const shouldShow = (hasValidPhone || hasContactPerson);
    contactPersonField.style.display = shouldShow ? 'block' : 'none';
    
    // Если есть контактное лицо, но нет телефона, показываем поле
    if (hasContactPerson && !hasValidPhone) {
      contactPersonField.style.display = 'block';
    }
  },

  parseContactDataOnLoad() {
    const relativePhoneInput = document.getElementById('relative_contact_phone');
    const contactPersonInput = document.getElementById('contact_person');
    
    if (!relativePhoneInput) return;
    
    // Сохраняем оригинальное значение до применения любых изменений
    const originalValue = relativePhoneInput.value;
    console.log('Original relative_contact_phone value:', originalValue);
    
    let phonePart = originalValue;
    let personPart = '';
    
    // Разбираем объединенные данные - используем регулярное выражение для надежности
    if (originalValue && originalValue.includes('&')) {
      // Используем индекс первого вхождения & для разделения
      const ampIndex = originalValue.indexOf('&');
      phonePart = originalValue.substring(0, ampIndex).trim();
      personPart = originalValue.substring(ampIndex + 1).trim();
      console.log('Parsed with "&":', { phonePart, personPart });
    } else {
      console.log('No "&" separator found, using whole value as phone');
    }
    
    // Устанавливаем значения в поля
    relativePhoneInput.value = phonePart;
    if (contactPersonInput) {
      contactPersonInput.value = personPart;
      console.log('Set contact_person to:', personPart);
    }
    
    // Обновляем отображение поля контактного лица
    this.toggleContactPersonField();
  },

  combineContactDataBeforeSubmit() {
    const relativePhoneInput = document.getElementById('relative_contact_phone');
    const contactPersonInput = document.getElementById('contact_person');
    
    if (!relativePhoneInput) return;
    
    let phoneValue = relativePhoneInput.value.trim();
    const personValue = contactPersonInput ? contactPersonInput.value.trim() : '';
    
    console.log('Before combine - phone:', phoneValue, 'person:', personValue);
    
    // Очищаем от предыдущих объединений (на всякий случай)
    if (phoneValue.includes('&')) {
      phoneValue = phoneValue.split('&')[0].trim();
    }
    
    // Объединяем только если есть контактное лицо
    if (personValue && personValue !== '') {
      relativePhoneInput.value = `${phoneValue}&${personValue}`;
    } else {
      relativePhoneInput.value = phoneValue;
    }
    
    console.log('After combine:', relativePhoneInput.value);
  },

  // ==================== ЛОГИКА ДИАГНОЗОВ ====================
  

  toggleDoctorFields() {
    const doctorId = document.getElementById('doctor_id');
    const newDoctorFields = document.getElementById('newDoctorFields');
    
    if (!doctorId || !newDoctorFields) return;

    // Используем только классы Bootstrap
    if (doctorId.value === "0") {
      newDoctorFields.classList.remove('d-none');
    } else {
      newDoctorFields.classList.add('d-none');
      const doctorFullName = document.getElementById('doctor_full_name');
      if (doctorFullName) doctorFullName.value = '';
    }
  },

  

  initDiagnosisSelect() {
    const select = document.getElementById('diagnosis_select');
    if (!select) return;

    const defaultDiagnosisId = select.dataset.defaultDiagnosisId;
    
    fetch("/api/diagnoses")
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        if (typeof $ !== 'undefined' && $.fn.select2) {
          $(select).select2({
            theme: "bootstrap-5",
            placeholder: "Выберите диагноз",
            allowClear: true,
            data: data,
            language: "ru"
          });

          let selectedId = null;
          if (defaultDiagnosisId && defaultDiagnosisId !== 'None') {
            const existsInData = data.find(item => item.id == defaultDiagnosisId);
            if (existsInData) selectedId = defaultDiagnosisId;
          }
          
          if (!selectedId && data.length > 0) selectedId = data[0].id;
          if (selectedId) $(select).val(selectedId).trigger('change');
        }
      })
      .catch(error => console.error("Ошибка загрузки диагнозов:", error));
  },

  // ==================== ЛОГИКА АВТОДОПОЛНЕНИЯ И ВАЛИДАЦИИ ВРАЧЕЙ ====================
  initDoctorAutocomplete() {
    const doctorInput = document.getElementById("doctor_name");
    const suggestionsBox = document.getElementById("doctor-suggestions");
    const areaSelect = document.getElementById("area_id");
    
    if (!doctorInput || !suggestionsBox) return;

    let currentIndex = -1;
    let currentSuggestions = [];

    doctorInput.addEventListener("input", function() {
      const query = doctorInput.value.trim();
      
      // Убираем валидацию при вводе - только автодополнение
      if (query.length < 2) {
        suggestionsBox.style.display = 'none';
        suggestionsBox.innerHTML = "";
        return;
      }

      fetch(`/api/search/doctors?q=${encodeURIComponent(query)}&limit=10`)
        .then(res => {
          if (!res.ok) throw new Error('Network response was not ok');
          return res.json();
        })
        .then(data => {
          suggestionsBox.innerHTML = "";
          currentIndex = -1;
          currentSuggestions = data;
          
          if (data.length > 0) {
            data.forEach((suggestion, idx) => {
              const item = document.createElement("div");
              item.classList.add("list-group-item", "list-group-item-action");
              
              let areaInfo = '';
              if (suggestion.area_name) {
                areaInfo = ` <span class="text-muted">(${suggestion.area_name})</span>`;
              }
              
              item.innerHTML = `${suggestion.value}${areaInfo}`;
              item.dataset.areaId = suggestion.area_id;

              item.addEventListener("mouseenter", () => {
                ApplicationCore.clearActiveSuggestions(suggestionsBox);
                currentIndex = idx;
                item.classList.add("active");
              });

              item.addEventListener("click", () => {
                doctorInput.value = suggestion.value;
                if (suggestion.area_id && areaSelect) {
                  areaSelect.value = suggestion.area_id;
                }
                suggestionsBox.style.display = 'none';
                suggestionsBox.innerHTML = "";
                // Валидация после выбора из автодополнения
                ApplicationCore.validateDoctorName();
              });

              suggestionsBox.appendChild(item);
            });
            suggestionsBox.style.display = 'block';
          } else {
            suggestionsBox.style.display = 'none';
          }
        })
        .catch(err => console.error('Error fetching doctor suggestions:', err));
    });

    doctorInput.addEventListener("keydown", function(e) {
      const items = suggestionsBox.querySelectorAll(".list-group-item");
      if (!items.length) return;

      if (e.key === "ArrowDown") {
        currentIndex = (currentIndex + 1) % items.length;
        ApplicationCore.updateActiveSuggestion(items, currentIndex);
        e.preventDefault();
      } else if (e.key === "ArrowUp") {
        currentIndex = (currentIndex - 1 + items.length) % items.length;
        ApplicationCore.updateActiveSuggestion(items, currentIndex);
        e.preventDefault();
      } else if (e.key === "Enter") {
        if (currentIndex >= 0 && items[currentIndex]) {
          const suggestion = currentSuggestions[currentIndex];
          doctorInput.value = suggestion.value;
          if (suggestion.area_id && areaSelect) {
            areaSelect.value = suggestion.area_id;
          }
          suggestionsBox.style.display = 'none';
          suggestionsBox.innerHTML = "";
          ApplicationCore.validateDoctorName();
          e.preventDefault();
        } else {
          // Если просто нажали Enter без выбора из списка - валидируем
          ApplicationCore.validateDoctorName();
        }
      } else if (e.key === "Escape") {
        suggestionsBox.style.display = 'none';
        suggestionsBox.innerHTML = "";
      }
    });

    // ВАЛИДАЦИЯ ПРИ ЗАВЕРШЕНИИ ВВОДА
    doctorInput.addEventListener("blur", () => {
      // Автоформатирование при потере фокуса
      ApplicationCore.formatDoctorName();
      // Валидация после форматирования
      ApplicationCore.validateDoctorName();
    });

    // Валидация при изменении значения через другие способы (например, вставка)
    doctorInput.addEventListener("change", () => {
      ApplicationCore.validateDoctorName();
    });

    document.addEventListener("click", function(e) {
      if (e.target !== doctorInput && !suggestionsBox.contains(e.target)) {
        suggestionsBox.style.display = 'none';
      }
    });

    // Инициализация валидации при загрузке, если поле уже заполнено
    if (doctorInput.value.trim() !== '') {
      ApplicationCore.validateDoctorName();
    }
  },

  // Автоформатирование ФИО врача
  formatDoctorName() {
    const doctorInput = document.getElementById('doctor_name');
    if (!doctorInput) return;

    let name = doctorInput.value.trim();
    if (name === '') return;

    name = name.replace(/\s+/g, ' ').trim();
    const parts = name.split(' ');
    
    if (parts.length < 2) return;

    // Форматируем фамилию (первая часть)
    let surname = parts[0];
    surname = surname.charAt(0).toUpperCase() + surname.slice(1).toLowerCase();

    // Обрабатываем инициалы (все остальные части)
    let initialsPart = parts.slice(1).join('');
    
    // Удаляем все точки и пробелы из инициалов
    const cleanInitials = initialsPart.replace(/[\.\s]/g, '');
    
    // Форматируем инициалы: каждую букву делаем заглавной и добавляем точку
    let formattedInitials = '';
    for (let i = 0; i < cleanInitials.length && i < 2; i++) { // Ограничиваем 2 инициалами
      formattedInitials += cleanInitials.charAt(i).toUpperCase() + '.';
    }

    const formattedName = surname + ' ' + formattedInitials;
    
    // Обновляем значение только если оно изменилось
    if (formattedName !== name) {
      doctorInput.value = formattedName;
    }
  },

  // Валидация ФИО врача
  validateDoctorName() {
    const doctorInput = document.getElementById('doctor_name');
    if (!doctorInput) return true;

    const doctorNameValue = doctorInput.value.trim();
    
    // Очистка предыдущих состояний валидации
    doctorInput.classList.remove('is-valid', 'is-invalid');
    this.clearValidationFeedback(doctorInput);
    
    // Если поле пустое - показываем ошибку только если оно было в фокусе
    if (doctorNameValue === '') {
      // Не показываем ошибку для пустого поля при загрузке, только после взаимодействия
      if (doctorInput.dataset.wasFocused === 'true') {
        this.showValidationError(doctorInput, 'ФИО врача обязательно для заполнения');
      }
      return false;
    }
    
    // Проверка формата: Фамилия И.О. или Фамилия И О
    const validFormats = [
      /^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.[А-ЯЁ]\.$/,      // Фамилия И.О.
      /^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.[А-ЯЁ]$/,       // Фамилия И.О (без последней точки)
      /^[А-ЯЁ][а-яё-]+\s[А-ЯЁ]\.[А-ЯЁ]\.$/,   // Фамилия с дефисом
      /^[А-ЯЁ][а-яё]+\s[А-ЯЁ]{2}$/,            // Фамилия ИО (без точек)
      /^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\s[А-ЯЁ]$/,      // Фамилия И О (с пробелом)
      /^[А-ЯЁ][а-яё]+\s[А-ЯЁ]\s[А-ЯЁ]\.$/     // Фамилия И О. (частично с точками)
    ];
    
    const isValidFormat = validFormats.some(regex => regex.test(doctorNameValue));
    
    if (!isValidFormat) {
      this.showValidationError(doctorInput, 'Используйте формат: Фамилия И.О.');
      return false;
    }
    
    this.showValidationSuccess(doctorInput, '✓ Формат корректен');
    return true;
  },

  // Очистка сообщений валидации
  clearValidationFeedback(field) {
    // Удаляем все сообщения обратной связи
    const parent = field.parentNode;
    const existingFeedback = parent.querySelectorAll('.valid-feedback, .invalid-feedback');
    existingFeedback.forEach(element => element.remove());
  },

  // Показать ошибку валидации
  showValidationError(field, message) {
    field.classList.remove('is-valid');
    field.classList.add('is-invalid');
    this.clearValidationFeedback(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
  },

  // Показать успешную валидацию
  showValidationSuccess(field, message) {
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
    this.clearValidationFeedback(field);
    
    const successDiv = document.createElement('div');
    successDiv.className = 'valid-feedback';
    successDiv.textContent = message;
    field.parentNode.appendChild(successDiv);
  },

  // Валидация формы перед отправкой
  initFormValidation() {
    const form = document.querySelector('form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
      // Принудительная валидация всех полей перед отправкой
      const isDoctorValid = ApplicationCore.validateDoctorName();
      const isContactPhoneValid = ApplicationCore.validatePhoneField(document.getElementById('contact_phone'));
      const isRelativePhoneValid = ApplicationCore.validatePhoneField(document.getElementById('relative_contact_phone'));
      const isAddressValid = ApplicationCore.validateAddressField(true); // Принудительная валидация при отправке
      
      let errorMessages = [];
      
      if (!isDoctorValid) {
        errorMessages.push('ФИО врача');
      }
      if (!isContactPhoneValid) {
        errorMessages.push('контактный телефон');
      }
      if (!isRelativePhoneValid) {
        errorMessages.push('телефон родственника');
      }
      if (!isAddressValid) {
        errorMessages.push('адрес');
      }
      
      if (errorMessages.length > 0) {
        e.preventDefault();
        const errorMessage = `Пожалуйста, исправьте ошибки в следующих полях: ${errorMessages.join(', ')}`;
        this.showFormError(errorMessage);
        
        // Прокручиваем к первому полю с ошибкой
        const firstErrorField = document.querySelector('.is-invalid');
        if (firstErrorField) {
          firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
          firstErrorField.focus();
        }
      }
    });
  },

  // Показать общую ошибку формы
  showFormError(message) {
    // Удаляем предыдущее сообщение
    const existingError = document.getElementById('form-validation-error');
    if (existingError) {
      existingError.remove();
    }
    
    const form = document.querySelector('form');
    if (!form) return;
    
    const errorDiv = document.createElement('div');
    errorDiv.id = 'form-validation-error';
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
      <strong>Ошибка!</strong> ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Вставляем в начало формы
    form.insertBefore(errorDiv, form.firstChild);
  },

  initDisinfectorAutocomplete() {
    const disinfectorInput = document.getElementById("disinfectors_input");
    const suggestionsBox = document.getElementById("disinfectors-suggestions");
    
    if (!disinfectorInput || !suggestionsBox) return;

    let currentIndex = -1;
    let currentSuggestions = [];

    disinfectorInput.addEventListener("input", function() {
        const query = disinfectorInput.value.trim();
        
        // Ищем последнюю запятую для автодополнения текущего имени
        const lastCommaIndex = query.lastIndexOf(',');
        const currentName = lastCommaIndex >= 0 ? query.substring(lastCommaIndex + 1).trim() : query;
        
        if (currentName.length < 2) {
            suggestionsBox.style.display = 'none';
            suggestionsBox.innerHTML = "";
            return;
        }

        fetch(`/api/search/disinfectors?q=${encodeURIComponent(currentName)}&limit=5`)
            .then(res => {
                if (!res.ok) throw new Error('Network response was not ok');
                return res.json();
            })
            .then(data => {
                suggestionsBox.innerHTML = "";
                currentIndex = -1;
                currentSuggestions = data;
                
                if (data.length > 0) {
                    data.forEach((suggestion, idx) => {
                        const item = document.createElement("div");
                        item.classList.add("list-group-item", "list-group-item-action");
                        item.textContent = suggestion.full_name;

                        item.addEventListener("mouseenter", () => {
                            ApplicationCore.clearActiveSuggestions(suggestionsBox);
                            currentIndex = idx;
                            item.classList.add("active");
                        });

                        item.addEventListener("click", () => {
                            // Заменяем текущее имя на выбранное
                            if (lastCommaIndex >= 0) {
                                const prefix = query.substring(0, lastCommaIndex + 1);
                                disinfectorInput.value = prefix + " " + suggestion.full_name;
                            } else {
                                disinfectorInput.value = suggestion.full_name;
                            }
                            suggestionsBox.style.display = 'none';
                            suggestionsBox.innerHTML = "";
                        });

                        suggestionsBox.appendChild(item);
                    });
                    suggestionsBox.style.display = 'block';
                } else {
                    suggestionsBox.style.display = 'none';
                }
            })
            .catch(err => console.error('Error fetching disinfector suggestions:', err));
    });

    disinfectorInput.addEventListener("keydown", function(e) {
        const items = suggestionsBox.querySelectorAll(".list-group-item");
        if (!items.length) return;

        if (e.key === "ArrowDown") {
            currentIndex = (currentIndex + 1) % items.length;
            ApplicationCore.updateActiveSuggestion(items, currentIndex);
            e.preventDefault();
        } else if (e.key === "ArrowUp") {
            currentIndex = (currentIndex - 1 + items.length) % items.length;
            ApplicationCore.updateActiveSuggestion(items, currentIndex);
            e.preventDefault();
        } else if (e.key === "Enter") {
            if (currentIndex >= 0 && items[currentIndex]) {
                const suggestion = currentSuggestions[currentIndex];
                const lastCommaIndex = this.value.lastIndexOf(',');
                
                if (lastCommaIndex >= 0) {
                    const prefix = this.value.substring(0, lastCommaIndex + 1);
                    this.value = prefix + " " + suggestion.full_name;
                } else {
                    this.value = suggestion.full_name;
                }
                suggestionsBox.style.display = 'none';
                suggestionsBox.innerHTML = "";
                e.preventDefault();
            }
        } else if (e.key === "Escape") {
            suggestionsBox.style.display = 'none';
            suggestionsBox.innerHTML = "";
        }
    });

    document.addEventListener("click", function(e) {
        if (e.target !== disinfectorInput && !suggestionsBox.contains(e.target)) {
            suggestionsBox.style.display = 'none';
        }
    });
},



  // ==================== ОБЩИЕ ФУНКЦИИ ФОРМ ====================
  toggleReasonField() {
    const userTypeSelect = document.getElementById("reason_application");
    const dateField = document.getElementById("dateField");
    const placeField = document.getElementById("placeFeald");

    if (!userTypeSelect) return;

    const toggleFields = () => {
      const isHospitalization = userTypeSelect.value === "hospitalization";
      if (dateField) dateField.style.display = isHospitalization ? "block" : "none";
      if (placeField) placeField.style.display = isHospitalization ? "block" : "none";
    };

    userTypeSelect.addEventListener("change", toggleFields);
    toggleFields();
  },

  

  // ==================== ОБНОВЛЕНИЕ ТЕКСТОВЫХ ЭЛЕМЕНТОВ ====================
  initTextUpdaters() {
    this.updateTextElements();
  },

  updateTextElements() {
    this.updateApplicationTexts();
    this.updateUserTexts();
  },

  updateApplicationTexts() {
    const elements = [
      { value: 'total-applications', text: 'total-text', words: ["заявка", "заявки", "заявок"] },
      { value: 'application-in-progress', text: 'in-progress-text', words: ["заявка", "заявки", "заявок"] },
      { value: 'applications-completed', text: 'completed-text', words: ["заявка", "заявки", "заявок"] }
    ];

    elements.forEach(({ value, text, words }) => {
      const valueElement = document.getElementById(value);
      const textElement = document.getElementById(text);
      
      if (valueElement && textElement) {
        const count = parseInt(valueElement.textContent, 10) || 0;
        textElement.textContent = declensionWord(count, words);
      }
    });
  },

  updateUserTexts() {
    const elements = [
      { value: 'total-users', text: 'users-text', words: ["пользователь", "пользователя", "пользователей"] },
      { value: 'adminCount', text: 'admins-count-text', words: ["администратор", "администратора", "администраторов"] },
      { value: 'doctorCount', text: 'doctors-count-text', words: ["врач", "врача", "врачей"] },
      { value: 'disinfectorCount', text: 'disinfectors-count-text', words: ["дезинфектор", "дезинфектора", "дезинфекторов"] }
    ];

    elements.forEach(({ value, text, words }) => {
      const valueElement = document.getElementById(value);
      const textElement = document.getElementById(text);
      
      if (valueElement && textElement) {
        const count = parseInt(valueElement.textContent, 10) || 0;
        textElement.textContent = declensionWord(count, words);
      }
    });
  },

  // ==================== ДАШБОРД КОМПОНЕНТЫ ====================
  initDashboardComponents() {
    if (typeof initDashboard === 'function') {
      initDashboard();
    }
  }
};

ApplicationCore.loadingMessages = [
  "🔍 Проверяем изменения...",
  "📨 Отправляем обновленные данные...",
  "⚡ Обрабатываем информацию...",
  "🦠 Проверяем эпидемиологические данные...",
  "📋 Обновляем документы дезинфекции...",
  "⏳ Завершаем обработку...",
  "✅ Почти готово..."
];

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application template DOM loaded - initializing ApplicationCore');
    ApplicationCore.init();
});

// Экспорт для глобального использования
window.applicationCore = ApplicationCore;