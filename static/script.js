class WebhookMonitor {
    constructor() {
        this.isConnected = false;
        this.lastUpdated = null;
        this.updateInterval = 15000; // 15 seconds
        this.intervalId = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.startPolling();
        this.fetchActions();
    }
    
    bindEvents() {
        const refreshBtn = document.getElementById('refresh-btn');
        refreshBtn.addEventListener('click', () => this.fetchActions());
    }
    
    startPolling() {
        this.intervalId = setInterval(() => {
            this.fetchActions();
        }, this.updateInterval);
    }
    
    stopPolling() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    
    async fetchActions() {
        try {
            const response = await fetch('/api/actions');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const actions = await response.json();
            this.updateUI(actions);
            this.updateStatus(true);
            
        } catch (error) {
            console.error('Error fetching actions:', error);
            this.updateStatus(false);
        }
    }
    
    updateUI(actions) {
        const actionsList = document.getElementById('actions-list');
        const emptyState = document.getElementById('empty-state');
        
        if (actions.length === 0) {
            actionsList.innerHTML = '<div class="loading">No activities yet</div>';
            emptyState.style.display = 'block';
            return;
        }
        
        emptyState.style.display = 'none';
        
        const actionsHTML = actions.map(action => {
            const iconType = action.type.toLowerCase();
            const iconText = this.getIconText(action.type);
            const timeAgo = this.formatTimeAgo(action.timestamp);
            
            return `
                <div class="action-item">
                    <div class="action-icon ${iconType}">
                        ${iconText}
                    </div>
                    <div class="action-content">
                        <div class="action-message">${action.message}</div>
                        <div class="action-time">${timeAgo}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        actionsList.innerHTML = actionsHTML;
    }
    
    getIconText(type) {
        switch (type.toLowerCase()) {
            case 'push':
                return '↑';
            case 'pull_request':
                return 'PR';
            case 'merge':
                return '⚡';
            default:
                return '•';
        }
    }
    
    formatTimeAgo(timestamp) {
        const now = new Date();
        const actionTime = new Date(timestamp);
        const diffInSeconds = Math.floor((now - actionTime) / 1000);
        
        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        }
    }
    
    updateStatus(connected) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.getElementById('status-text');
        const lastUpdated = document.getElementById('last-updated');
        
        this.isConnected = connected;
        
        if (connected) {
            statusDot.classList.remove('disconnected');
            statusText.textContent = 'Connected';
            this.lastUpdated = new Date();
            lastUpdated.textContent = this.lastUpdated.toLocaleTimeString();
        } else {
            statusDot.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
        }
    }
}

// Initialize the monitor when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new WebhookMonitor();
});