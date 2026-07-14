// Toast Notification System - только по клику на колокольчик
class ToastNotificationManager {
    constructor() {
        this.unreadCount = 0;
        this.isLoading = false;
        this.socket = null;
        this.visibleToasts = new Set();
        this.init();
    }

    init() {
        this.createToastContainer();
        this.initializeSocket();
        this.setupEventListeners();
        this.updateUnreadCount();
    }

    createToastContainer() {
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
    }

    initializeSocket() {
        try {
            this.socket = io({
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000
            });

            this.setupSocketHandlers();
            
        } catch (error) {
            console.error('❌ Failed to initialize Socket.IO:', error);
        }
    }

    setupSocketHandlers() {
        if (!this.socket) return;
        
        this.socket.on('connect', () => {
            console.log('✅ WebSocket connected for notifications');
            this.identifyUser();
        });

        this.socket.on('new_notification', (data) => {
            console.log('📢 New notification received:', data);
            // Только обновляем счетчик, не показываем тосты автоматически
            this.updateUnreadCount();
        });

        // Обработчик удаления уведомления
        this.socket.on('notification_cleaned', (data) => {
            console.log('🗑️ Notification cleaned:', data);
            this.closeToast(data.notification_id, false);
        });
    }

    identifyUser() {
        if (window.currentUserId && this.socket) {
            this.socket.emit('identify', {
                user_type: window.currentUserType,
                user_id: window.currentUserId
            });
        }
    }

    setupEventListeners() {
        // Обработчик клика на колокольчик - показываем непрочитанные уведомления
        const bellButton = document.querySelector('.notification-bell');
        if (bellButton) {
            bellButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.showUnreadNotifications();
            });
        }

        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.updateUnreadCount();
            }
        });
    }

    async showUnreadNotifications() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        try {
            const response = await fetch('/api/notifications?unread_only=true&limit=10');
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            
            // Очищаем предыдущие тосты
            this.closeAllToasts();
            
            // Показываем новые непрочитанные уведомления
            data.notifications.forEach(notification => {
                if (!this.visibleToasts.has(notification.id)) {
                    this.showToast(notification);
                }
            });

        } catch (error) {
            console.error('Error loading unread notifications:', error);
        } finally {
            this.isLoading = false;
        }
    }

    showToast(notification) {
        if (this.visibleToasts.has(notification.id)) {
            return;
        }

        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.dataset.notificationId = notification.id;

        toast.innerHTML = `
            <div class="toast-header">
                <div class="toast-title">
                    <i class="fas ${this.getNotificationIcon(notification.type)} me-2"></i>
                    ${this.escapeHtml(notification.title)}
                </div>
                <button type="button" class="btn-close" onclick="toastNotificationManager.closeToast('${notification.id}', true)"></button>
            </div>
            <div class="toast-body">
                <div class="toast-message">
                    ${this.escapeHtml(notification.message)}
                </div>
                <div class="toast-time small text-muted mt-2">
                    ${this.formatTime(notification.created_at)}
                </div>
                <div class="toast-actions">
                    <button class="btn-toast btn-toast-success"
                            onclick="toastNotificationManager.markAsReadAndReload('${notification.id}')">
                        <i class="fas fa-check me-1"></i>Прочитано
                    </button>
                    <button class="btn-toast btn-toast-primary"
                            onclick="toastNotificationManager.markAllAsReadAndReload()">
                        <i class="fas fa-check-double me-1"></i>Прочитать все
                    </button>
                </div>
            </div>
        `;

        const container = document.getElementById('toast-container');
        container.appendChild(toast);

        this.visibleToasts.add(notification.id);

        // Автоматическое закрытие через 10 секунд
        setTimeout(() => {
            this.closeToast(notification.id, false);
        }, 10000);
    }

    async markAsReadAndReload(notificationId) {
        try {
            // Помечаем как прочитанное
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                // Обновляем счетчик
                this.updateUnreadCount();
                
                // Закрываем тост
                this.closeToast(notificationId, false);
                
                // Обновляем страницу через 500ms для плавного перехода
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    async markAllAsReadAndReload() {
        try {
            const response = await fetch('/api/notifications/read-all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                // Обновляем счетчик
                this.updateUnreadCount();
                
                // Закрываем все тосты
                this.closeAllToasts();
                
                // Обновляем страницу через 500ms для плавного перехода
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    }

    closeToast(notificationId, markAsRead = false) {
        const toast = document.querySelector(`[data-notification-id="${notificationId}"]`);
        if (toast) {
            toast.classList.add('toast-hiding');
            
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
                this.visibleToasts.delete(notificationId);
            }, 300);

            if (markAsRead) {
                this.markAsRead(notificationId);
            }
        }
    }

    async updateUnreadCount() {
        try {
            const response = await fetch('/api/notifications/unread-count');
            if (response.ok) {
                const data = await response.json();
                this.updateBadge(data.unread_count);
            }
        } catch (error) {
            console.error('Error updating unread count:', error);
        }
    }

    updateBadge(count) {
        this.unreadCount = count;
        const badge = document.querySelector('.notification-count');
        const bell = document.querySelector('.notification-bell');
        
        if (count > 0) {
            if (badge) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'flex';
            }
            if (bell) {
                bell.classList.add('has-notifications');
            }
        } else {
            if (badge) {
                badge.style.display = 'none';
            }
            if (bell) {
                bell.classList.remove('has-notifications');
            }
        }
    }

    closeAllToasts() {
        document.querySelectorAll('.toast-notification').forEach(toast => {
            const notificationId = toast.dataset.notificationId;
            this.closeToast(notificationId, false);
        });
    }

    getNotificationIcon(type) {
        const icons = {
            'new_application': 'fa-file-medical text-primary',
            'status_update': 'fa-sync-alt text-warning',
            'application_updated': 'fa-edit text-info',
            'info': 'fa-info-circle text-secondary'
        };
        return icons[type] || 'fa-bell text-secondary';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'только что';
        if (diffMins < 60) return `${diffMins} мин. назад`;
        if (diffHours < 24) return `${diffHours} ч. назад`;
        if (diffDays < 7) return `${diffDays} дн. назад`;
        
        return date.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    window.toastNotificationManager = new ToastNotificationManager();
    
    // // Добавляем глобальную функцию для массового прочтения
    // window.markAllNotificationsRead = function() {
    //     if (window.toastNotificationManager) {
    //         window.toastNotificationManager.markAllAsReadAndReload();
    //     }
    // };
});