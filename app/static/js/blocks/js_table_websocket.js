// Автоматическое обновление таблицы заявок через WebSocket
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, есть ли таблица заявок на странице
    const applicationsTable = document.getElementById('myTableApplications') || 
                              document.getElementById('myTableDoctors') ||
                              document.getElementById('myTableAdmins');
    
    if (!applicationsTable || !window.toastNotificationManager || !window.toastNotificationManager.socket) {
        console.log('WebSocket table update: not initialized (no table or socket)');
        return;
    }
    
    const socket = window.toastNotificationManager.socket;
    
    // Слушаем событие обновления заявки
    socket.on('application_status_updated', function(data) {
        console.log('Application status updated:', data);
        
        // Находим DataTable
        const dataTable = $.fn.DataTable.isDataTable(applicationsTable) ? 
                          $(applicationsTable).DataTable() : null;
        
        if (dataTable) {
            // Перезагружаем таблицу без полной перезагрузки страницы
            dataTable.ajax.reload(null, false);
            console.log('Table refreshed via WebSocket');
        } else {
            // Если DataTable не инициализирован, просто перезагружаем страницу
            // Это временное решение
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    });
});
