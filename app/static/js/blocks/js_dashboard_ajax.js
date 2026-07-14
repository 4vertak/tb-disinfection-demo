
// Глобальные переменные для хранения экземпляров диаграмм
let monthlyChart, areasChart, focusChart, AreasChartDin, disinfectorsChart;
let currentView = 'monthly';

// Функция переключения вида
function switchDashboardView(viewType) {
  currentView = viewType;

  // Скрыть все контейнеры
  document.querySelectorAll('.tab-content').forEach(container => {
    container.classList.add('d-none');
    container.classList.remove('active');
  });

  // Показать выбранный контейнер
  const activeContainer = document.getElementById(`${viewType}Container`);
  if (activeContainer) {
    activeContainer.classList.remove('d-none');
    activeContainer.classList.add('active');
  }

  // Обновить активные кнопки
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');

    if (btn.dataset.view === viewType) {
      btn.classList.add('active');
    }
  });

  // Обновить графики
  updateChartsOnViewChange(viewType);
}

function updateChartsOnViewChange(viewType) {
  setTimeout(() => {
    switch(viewType) {
      case 'monthly':
        if (monthlyChart) {
          monthlyChart.resize();
          monthlyChart.update();
        }
        break;
      case 'areas':
        [areasChart, focusChart, AreasChartDin].forEach(chart => {
          if (chart) {
            chart.resize();
            chart.update();
          }
        });
        break;
      case 'disinfectors':
        if (disinfectorsChart) {
          disinfectorsChart.resize();
          disinfectorsChart.update();
        }
        break;
    }
  }, 100);
}

// Функция для загрузки данных через AJAX
function loadDashboardData(period, year) {
    showLoadingIndicator();
    
    // Обновляем URL без перезагрузки страницы
    const newUrl = `${window.location.pathname}?period=${encodeURIComponent(period)}&year=${year}`;
    window.history.pushState({}, '', newUrl);
    
    // Делаем запрос с задержкой для лучшего UX
    setTimeout(() => {
        fetch(`/dashboard/data?period=${encodeURIComponent(period)}&year=${year}`)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                // Небольшая задержка для плавности
                setTimeout(() => {
                    updateDashboard(data);
                    hideLoadingIndicator();

                    // Обновляем заголовок топ-дезинфекторов
                    // updateTopDisinfectorsTitle(period, year);
                    updateHeaderStats(period, year, data.top_disinfectors);
                    
                    // Обновляем ссылки экспорта
                    updateExportLinks(period, year);
                    
                    // После загрузки данных показать выбранный вид
                    switchDashboardView(currentView);
                }, 300);
            })
            .catch(error => {
                console.error('Error loading dashboard data:', error);
                hideLoadingIndicator();
                showErrorToast('Ошибка при загрузке данных. Попробуйте еще раз.');
            });
    }, 200);
}


// Функция для показа уведомления об ошибке
function showErrorToast(message) {
    // Создаем уведомление Bootstrap
    const toast = document.createElement('div');
    toast.className = 'toast align-items-center text-bg-danger border-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-exclamation-triangle me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    const container = document.querySelector('.toast-container');
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(newContainer);
        container = newContainer;
    }
    
    container.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Удаляем уведомление через 5 секунд
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Функция для обновления всех элементов дашборда
function updateDashboard(data) {
    updateStats(data.total_info);
    updateCharts(data);
    updateTable(data.table_data);
    // Обновляем карточки топ-3 дезинфекторов
    if (data.top_disinfectors) {
        updateTopDisinfectorsCards(data.top_disinfectors);
    }
}



// Функция для обновления статистических блоков
function updateStats(totalInfo) {
    const totalElement = document.getElementById('total-applications');
    const inProgressElement = document.getElementById('application-in-progress');
    const completedElement = document.getElementById('applications-completed');
    const refusalElement = document.getElementById('applications-refusal');
    const carryOverElement = document.getElementById('carry-over-applications');

    // Обновляем общее количество с учетом переходящих
    const totalWithCarryOver = totalInfo.total_with_carry_over !== undefined ? 
        totalInfo.total_with_carry_over : (totalInfo.total || 0);
    
    if (totalElement) totalElement.textContent = totalWithCarryOver;
    if (inProgressElement) inProgressElement.textContent = totalInfo.in_progress !== undefined ? totalInfo.in_progress : 0;
    if (completedElement) completedElement.textContent = totalInfo.completed !== undefined ? totalInfo.completed : 0;
    if (refusalElement) refusalElement.textContent = totalInfo.refusal !== undefined ? totalInfo.refusal : 0;
    
    // Обновляем badge с переходящими заявками
    const carryOver = totalInfo.carry_over !== undefined ? totalInfo.carry_over : 0;
    if (carryOverElement) carryOverElement.textContent = carryOver;
    
    // Обновляем все badge на странице
    document.querySelectorAll('[id*="carry-over"]').forEach(el => {
        if (el.id !== 'carry-over-applications') {
            el.textContent = carryOver;
        }
    });

    const carryOverSpan = document.getElementById('carry-over-applications');
    if (carryOverSpan) {
        const val = totalInfo.carry_over || 0;
        carryOverSpan.textContent = val;
        const badge = carryOverSpan.closest('.badge');
        if (badge) {
            badge.style.display = val > 0 ? 'inline-block' : 'none';
        }
    }

    // Обновляем блок площади только если он есть на странице
    const squareElement = document.getElementById('square-disinfection');
    if (squareElement) {
        squareElement.textContent = totalInfo.square_disinfection !== undefined ?
            parseFloat(totalInfo.square_disinfection).toFixed(1) : '0.0';
    }
}

// Функция для обновления всех диаграмм
function updateCharts(data) {
    // Всегда обновляем данные, но рендерим в зависимости от вида
    updateMonthlyChart(data);
    updateAreasChart(data);
    updateFocusChart(data);
    updateAreasChartDin(data);
    
    // if (data.top_disinfectors && data.top_disinfectors.length > 0) {
        updateDisinfectorsChart(data);
    // }
    
    // Показать/скрыть в зависимости от текущего вида
    switchDashboardView(currentView);
}

// Функция для обновления месячной диаграммы
function updateMonthlyChart(data) {
    if (monthlyChart) {
        // Сохраняем текущие значения для анимации
        const oldData = {
            labels: monthlyChart.data.labels || [],
            total_values: monthlyChart.data.datasets[0].data || [],
            completed_values: monthlyChart.data.datasets[1].data || []
        };
        
        // Обновляем данные
        monthlyChart.data.labels = data.months;
        monthlyChart.data.datasets[0].data = data.total_values;
        monthlyChart.data.datasets[1].data = data.completed_values;
        
        // Анимация обновления
        monthlyChart.update({
            duration: 800,
            easing: 'easeOutQuart',
            lazy: false
        });
    } else {
        initializeMonthlyChart(data);
    }
}

function initializeMonthlyChart(data) {
    const ctxMonthly = document.getElementById('monthlyChart');
    if (!ctxMonthly) return;
    
    const config = window.chartConfigs.monthly;
    monthlyChart = new Chart(ctxMonthly.getContext('2d'), {
        type: config.type,
        data: {
            labels: data.months,
            datasets: config.datasets.map((dataset, index) => ({
                ...dataset,
                data: index === 0 ? data.total_values : data.completed_values
            }))
        },
        options: config.options
    });
}

// Функция для обновления диаграммы участков (полярная)
function updateAreasChart(data) {
    if (areasChart) {
        // Сохраняем старые данные для анимации
        const oldLabels = areasChart.data.labels || [];
        const oldData = areasChart.data.datasets[0].data || [];
        
        // Обновляем данные
        areasChart.data.labels = data.areas_labels;
        areasChart.data.datasets[0].data = data.areas_total_values;
        
        // Плавная анимация
        areasChart.update({
            duration: 800,
            easing: 'easeOutQuart',
            animation: {
                animateRotate: true,
                animateScale: true
            }
        });
    } else {
        initializeAreasChart(data);
    }
}

function initializeAreasChart(data) {
    const ctxAreas = document.getElementById('areasChart');
    if (!ctxAreas) return;
    
    const config = window.chartConfigs.areas;
    areasChart = new Chart(ctxAreas.getContext('2d'), {
        type: config.type,
        data: {
            labels: data.areas_labels,
            datasets: [{
                ...config.datasets[0],
                data: data.areas_total_values
            }]
        },
        options: config.options
    });
}

// Функция для обновления диаграммы фокусов
function updateFocusChart(data) {
    if (focusChart) {
        // Сохраняем старые данные
        const oldLabels = focusChart.data.labels || [];
        const oldDatasets = focusChart.data.datasets || [];
        
        // Обновляем данные
        focusChart.data.labels = data.focus_labels;
        focusChart.data.datasets = createFocusDatasets(data);
        
        // Анимация с задержкой для каждого бара
        focusChart.update({
            duration: 800,
            easing: 'easeOutQuart',
            animation: {
                duration: function(context) {
                    // Разная задержка для каждого бара для эффекта последовательности
                    return 600 + context.dataIndex * 50;
                }
            }
        });
    } else {
        initializeFocusChart(data);
    }
}

function initializeFocusChart(data) {
    const ctx = document.getElementById('focusChart');
    if (!ctx) return;
    
    const config = window.chartConfigs.focus;
    const colors = [
        'rgba(255, 99, 132, 0.5)',
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 206, 86, 0.5)',
        'rgba(75, 192, 192, 0.5)',
        'rgba(153, 102, 255, 0.5)',
        'rgba(255, 159, 64, 0.5)',
        'rgba(99, 255, 132, 0.5)',
        'rgba(162, 54, 235, 0.5)',
        'rgba(206, 86, 255, 0.5)',
        'rgba(192, 192, 75, 0.5)',
        'rgba(102, 255, 153, 0.5)',
        'rgba(159, 64, 255, 0.5)'
    ];
    
    focusChart = new Chart(ctx.getContext('2d'), {
        type: config.type,
        data: {
            labels: data.focus_labels,
            datasets: data.area_labelsf.map((area, index) => ({
                label: area,
                data: data.focus_total_values_list.map(values => values[index] || 0),
                backgroundColor: colors[index % colors.length],
                borderColor: colors[index % colors.length].replace('0.5', '1'),
                borderWidth: 1
            }))
        },
        options: config.options
    });
}

function createFocusDatasets(data) {
    const colors = [
        'rgba(255, 99, 132, 0.5)',
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 206, 86, 0.5)',
        'rgba(75, 192, 192, 0.5)',
        'rgba(153, 102, 255, 0.5)',
        'rgba(255, 159, 64, 0.5)',
        'rgba(99, 255, 132, 0.5)',
        'rgba(162, 54, 235, 0.5)',
        'rgba(206, 86, 255, 0.5)',
        'rgba(192, 192, 75, 0.5)',
        'rgba(102, 255, 153, 0.5)',
        'rgba(159, 64, 255, 0.5)'
    ];
    
    return data.area_labelsf.map((area, index) => ({
        label: area,
        data: data.focus_total_values_list.map(values => values[index] || 0),
        backgroundColor: colors[index % colors.length],
        borderColor: colors[index % colors.length].replace('0.5', '1'),
        borderWidth: 1
    }));
}

// Функция для обновления диаграммы участков (столбчатая)
function updateAreasChartDin(data) {
    if (AreasChartDin) {
        const oldLabels = AreasChartDin.data.labels || [];
        const oldTotalData = AreasChartDin.data.datasets[0].data || [];
        const oldCompletedData = AreasChartDin.data.datasets[1].data || [];
        
        // Обновляем данные
        AreasChartDin.data.labels = data.areas_labels;
        AreasChartDin.data.datasets[0].data = data.areas_total_values;
        AreasChartDin.data.datasets[1].data = data.areas_completed_values;
        
        // Анимация столбцов
        AreasChartDin.update({
            duration: 800,
            easing: 'easeOutQuart',
            animation: {
                duration: function(context) {
                    return 400 + context.dataIndex * 60;
                }
            }
        });
    } else {
        initializeAreasChartDin(data);
    }
}

function initializeAreasChartDin(data) {
    const ctxAreasDin = document.getElementById('AreasChartDin');
    if (!ctxAreasDin) return;
    
    const config = window.chartConfigs.areasDin;
    AreasChartDin = new Chart(ctxAreasDin.getContext('2d'), {
        type: config.type,
        data: {
            labels: data.areas_labels,
            datasets: config.datasets.map((dataset, index) => ({
                ...dataset,
                data: index === 0 ? data.areas_total_values : data.areas_completed_values
            }))
        },
        options: config.options
    });
}

// Функция для обновления диаграммы дезинфекторов
function updateDisinfectorsChart(data) {
    const ctx = document.getElementById('disinfectorsChart');
    if (!ctx) return;

    // Проверяем, есть ли данные
    if (!data.top_disinfectors || data.top_disinfectors.length === 0) {
        // Скрываем график, если нет данных
        ctx.style.display = 'none';
        const chartContainer = ctx.closest('.chart-container');
        if (chartContainer) {
            chartContainer.style.display = 'none';
        }
        return;
    } else {
        // Показываем график, если есть данные
        ctx.style.display = 'block';
        const chartContainer = ctx.closest('.chart-container');
        if (chartContainer) {
            chartContainer.style.display = 'block';
        }
    }

    if (disinfectorsChart) {
        const oldLabels = disinfectorsChart.data.labels || [];
        const oldCounts = disinfectorsChart.data.datasets[0].data || [];
        const oldAreas = disinfectorsChart.data.datasets[1].data || [];
        
        // Обновляем данные
        disinfectorsChart.data.labels = data.top_disinfectors.map(d => d.name);
        disinfectorsChart.data.datasets[0].data = data.top_disinfectors.map(d => d.disinfection_count);
        disinfectorsChart.data.datasets[1].data = data.top_disinfectors.map(d => d.total_area);
        
        // Анимация столбцов
        disinfectorsChart.update({
            duration: 800,
            easing: 'easeOutQuart',
            animation: {
                duration: function(context) {
                    return 500 + context.dataIndex * 80;
                }
            }
        });
    } else {
        initializeDisinfectorsChart(data);
    }
}

function initializeDisinfectorsChart(data) {
    const ctx = document.getElementById('disinfectorsChart');
    if (!ctx) return;
    
    // Проверяем, есть ли данные
    if (!data.top_disinfectors || data.top_disinfectors.length === 0) {
        // Можно отобразить сообщение об отсутствии данных
        ctx.style.display = 'none';
        return;
    }
    
    disinfectorsChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: data.top_disinfectors.map(d => d.name),
            datasets: [
                {
                    label: 'Количество дезинфекций',
                    data: data.top_disinfectors.map(d => d.disinfection_count),
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Обработанная площадь (м²)',
                    data: data.top_disinfectors.map(d => d.total_area),
                    backgroundColor: 'rgba(255, 99, 132, 0.7)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                    type: 'bar',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    // text: 'Статистика дезинфекторов по выполненным работам',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.datasetIndex === 0) {
                                label += context.parsed.y + ' заявок';
                            } else {
                                label += context.parsed.y.toFixed(1) + ' м²';
                            }
                            return label;
                        },
                        afterLabel: function(context) {
                            if (context.datasetIndex === 0) {
                                const disinfectorName = context.label;
                                const disinfectorData = data.top_disinfectors.find(d => d.name === disinfectorName);
                                if (disinfectorData && disinfectorData.total_area > 0) {
                                    const avgArea = disinfectorData.total_area / disinfectorData.disinfection_count;
                                    return `Средняя площадь на заявку: ${avgArea.toFixed(1)} м²`;
                                }
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 0
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Количество заявок'
                    },
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Площадь (м²)'
                    },
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        callback: function(value) {
                            return value.toFixed(0) + ' м²';
                        }
                    }
                }
            }
        }
    });
}

// Функция для обновления карточек топ-3 дезинфекторов
function updateTopDisinfectorsCards(topDisinfectors) {
    const container = document.querySelector('#disinfectorsContainer .row.g-4.justify-content-center');
    if (!container) return;

    let html = '';
    if (topDisinfectors && topDisinfectors.length > 0) {
        // Берем первые три элемента
        const topThree = topDisinfectors.slice(0, 3);
        topThree.forEach((disinfector, index) => {
            const rank = index + 1;
            let rankBadge = '';
            let iconClass = '';
            let borderClass = 'border-light';
            let bgClass = '';
            
            if (rank === 1) {
                rankBadge = `<span class="badge bg-warning text-dark fs-5 position-absolute top-0 start-50 translate-middle rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;">1</span>`;
                iconClass = 'fas fa-trophy text-warning fa-2x';
                borderClass = 'border-warning border-2';
                bgClass = 'bg-warning bg-opacity-10';
            } else if (rank === 2) {
                rankBadge = `<span class="badge bg-secondary fs-6 position-absolute top-0 start-50 translate-middle rounded-circle d-flex align-items-center justify-content-center" style="width: 35px; height: 35px;">2</span>`;
                iconClass = 'fas fa-medal text-secondary fa-2x';
                bgClass = 'bg-secondary bg-opacity-10';
            } else {
                rankBadge = `<span class="badge bg-danger fs-6 position-absolute top-0 start-50 translate-middle rounded-circle d-flex align-items-center justify-content-center" style="width: 35px; height: 35px;">3</span>`;
                iconClass = 'fas fa-award text-danger fa-2x';
                bgClass = 'bg-danger bg-opacity-10';
            }

            const avgArea = disinfector.disinfection_count > 0 ? 
                (disinfector.total_area / disinfector.disinfection_count).toFixed(1) : 0;

            html += `
            <div class="col-md-4">
                <div class="card h-100 border-0 shadow-sm ${borderClass}">
                    <div class="card-body text-center p-4">
                        <div class="position-relative mb-3">
                            <div class="d-flex justify-content-center align-items-center mb-3">
                                ${rankBadge}
                                <div class="rounded-circle ${bgClass} p-3">
                                    <i class="${iconClass}"></i>
                                </div>
                            </div>
                        </div>
                        
                        <h5 class="card-title mb-2">${disinfector.name}</h5>
                        
                        <div class="row text-center mt-3">
                            <div class="col-6">
                                <div class="p-2 bg-light rounded">
                                    <div class="text-primary fw-bold fs-4">${disinfector.disinfection_count}</div>
                                    <small class="text-muted">заявок</small>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="p-2 bg-light rounded">
                                    <div class="text-success fw-bold fs-4">${disinfector.total_area.toFixed(0)}</div>
                                    <small class="text-muted">м²</small>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <small class="text-muted">
                                <i class="fas fa-chart-line me-1"></i>
                                Средняя площадь: ${avgArea} м²
                            </small>
                        </div>
                    </div>
                </div>
            </div>`;
        });
    } else {
        html = `
        <div class="col-12">
            <div class="alert alert-info text-center">
                <i class="fas fa-info-circle me-2"></i>
                Нет данных о дезинфекторах за выбранный период
            </div>
        </div>`;
    }

    container.innerHTML = html;
}



// Функция для обновления заголовка топ-дезинфекторов
// function updateTopDisinfectorsTitle(period, year) {
//     updateHeaderStats(period, year);
// }

// Функция для обновления статистики в заголовке
function updateHeaderStats(period, year, topDisinfectors) {
    const statsContainer = document.querySelector('.header-stats .d-flex');
    if (!statsContainer) return;
    
    // Обновляем количество участников
    const participantsElement = statsContainer.querySelector('.stat-item:first-child span');
    if (participantsElement) {
        const count = topDisinfectors ? topDisinfectors.length : 0;
        participantsElement.textContent = `Всего:\u00A0${count}\u00A0чел.`;
    }
    
    const periodElement = statsContainer.querySelector('.stat-item:last-child span');
    if (periodElement) {
        if (period === 'год') {
            periodElement.textContent = `Период:\u00A0${year}\u00A0год`;
        } else {
            periodElement.textContent = `Период:\u00A0${period}\u00A0${year}\u00A0года`;
        }
    }
}


// Функция для обновления ссылок экспорта
function updateExportLinks(period, year) {
    
    // 1. Обновляем ссылку на экспорт в Excel (ищем по классу или data-атрибуту)
    
    const excelExportLinks = document.querySelectorAll('[data-export-type="excel"]');
    excelExportLinks.forEach(link => {
        link.href = `/import-export/export?period=${encodeURIComponent(period)}&year=${year}`;
        console.log('Updated Excel link (data-attr):', link.href);
    });
    
    // 2. Обновляем ссылку на скачивание Word-отчета
    const wordReportLink = document.getElementById('downloadReport');
    if (wordReportLink) {
        const oldHref = wordReportLink.href;
        wordReportLink.href = `/generate_word_report?period=${encodeURIComponent(period)}&year=${year}`;
        console.log('Updated Word link from', oldHref, 'to', wordReportLink.href);
    } else {
        console.error('Word report link not found!');
    }
}


// Функция для обновления таблицы
function updateTable(tableData) {
    const tableBody = document.querySelector('.table tbody');
    if (tableBody && tableData) {
        let html = '';
        
        tableData.forEach(row => {
            const isBold = row.focus.includes('ВСЕГО') || row.focus.includes('посмертно');
            html += `<tr class="${isBold ? 'font-weight-bold table' : 'table'}">`;
            html += `<td>${row.focus}</td>`;
            
            // Динамически добавляем колонки для всех участков
            const areas = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'ДПДО', 'РПТД'];
            areas.forEach(area => {
                html += `<td>${row[area] || 0}</td>`;
            });
            
            html += `<td>${row.total || 0}</td>`;
            html += `</tr>`;
        });
        
        tableBody.innerHTML = html;
    }
}

// Функция для обновления ссылки скачивания
function updateDownloadLink() {
    const downloadLink = document.getElementById('downloadReport');
    const periodSelect = document.getElementById('selectPeriod');
    const yearSelect = document.getElementById('selectYear');
    
    if (downloadLink && periodSelect && yearSelect) {
        const period = encodeURIComponent(periodSelect.value);
        const year = yearSelect.value;
        downloadLink.href = `/generate_word_report?period=${period}&year=${year}`;
        console.log('Download link updated:', downloadLink.href); // Для отладки
    }
}

// Функции для индикатора загрузки
function showLoadingIndicator() {
    const charts = document.querySelectorAll('canvas');
    charts.forEach(chart => {
        chart.classList.add('chart-loading');
        chart.style.opacity = '0.7';
    });
    
    // Статистические блоки
    const statBlocks = document.querySelectorAll('.p-4');
    statBlocks.forEach(block => {
        block.classList.add('chart-loading');
    });
    
    const loadingSpinner = document.createElement('div');
    loadingSpinner.id = 'loadingSpinner';
    loadingSpinner.innerHTML = `
        <div class="d-flex flex-column align-items-center">
            <div class="spinner-border text-primary mb-2" style="width: 3rem; height: 3rem;" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="text-muted">Загружаем данные...</p>
        </div>
    `;
    loadingSpinner.style.position = 'fixed';
    loadingSpinner.style.top = '50%';
    loadingSpinner.style.left = '50%';
    loadingSpinner.style.transform = 'translate(-50%, -50%)';
    loadingSpinner.style.zIndex = '9999';
    loadingSpinner.style.background = 'rgba(255, 255, 255, 0)';
    loadingSpinner.style.padding = '2rem';
    loadingSpinner.style.borderRadius = '10px';
    // loadingSpinner.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.1)';
    
    document.body.appendChild(loadingSpinner);
}

function hideLoadingIndicator() {
    const charts = document.querySelectorAll('canvas');
    charts.forEach(chart => {
        chart.classList.remove('chart-loading');
        chart.style.opacity = '1';
    });
    
    const statBlocks = document.querySelectorAll('.p-4');
    statBlocks.forEach(block => {
        block.classList.remove('chart-loading');
    });
    
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        // Плавное исчезновение
        loadingSpinner.style.opacity = '0';
        loadingSpinner.style.transition = 'opacity 0.3s ease';
        setTimeout(() => {
            loadingSpinner.remove();
        }, 300);
    }
}

// Инициализация обработчиков событий
function initDashboardEventListeners() {
    const periodSelect = document.getElementById('selectPeriod');
    const yearSelect = document.getElementById('selectYear');
    
    if (periodSelect && yearSelect) {
        // При изменении периода или года загружаем новые данные
        periodSelect.addEventListener('change', function() {
            loadDashboardData(this.value, yearSelect.value);
        });
        
        yearSelect.addEventListener('change', function() {
            loadDashboardData(periodSelect.value, this.value);
        });
    }
}

// Инициализация всех диаграмм с начальными данными
function initDashboardCharts(initialData) {
    if (initialData.monthly) initializeMonthlyChart(initialData.monthly);
    if (initialData.areas) initializeAreasChart(initialData.areas);
    if (initialData.focus) initializeFocusChart(initialData.focus);
    if (initialData.areasDin) initializeAreasChartDin(initialData.areasDin);
    if (initialData.disinfectors) initializeDisinfectorsChart(initialData.disinfectors);
}

// Основная функция инициализации
function initDashboard() {
  initDashboardEventListeners();

  if (window.dashboardInitialData) {
    initDashboardCharts(window.dashboardInitialData);
  }

  // Обработчики кликов для кнопок вкладок
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const viewType = this.dataset.view;
      switchDashboardView(viewType);
    });
  });

  // Установить вид по умолчанию
  const activeBtn = document.querySelector('.tab-btn.active');
  if (activeBtn) {
    switchDashboardView(activeBtn.dataset.view || 'monthly');
  } else {
    switchDashboardView('monthly');
  }
}

// Экспортируем функции для глобального использования
window.loadDashboardData = loadDashboardData;
window.initDashboard = initDashboard;
window.updateDashboard = updateDashboard;