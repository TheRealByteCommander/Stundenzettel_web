// Schmitz Intralogistik Zeiterfassung - Main Application JavaScript
class TimesheetApp {
    constructor() {
        this.currentUser = null;
        this.token = localStorage.getItem('token');
        this.apiBase = 'api';
        this.currentTab = 'timesheets';
        this.editingUserId = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        
        if (this.token) {
            this.validateToken();
        } else {
            this.showLogin();
        }
    }

    bindEvents() {
        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Tab navigation
        document.getElementById('tabTimesheets').addEventListener('click', () => {
            this.switchTab('timesheets');
        });
        
        document.getElementById('tabNewTimesheet').addEventListener('click', () => {
            this.switchTab('newTimesheet');
        });
        
        document.getElementById('tabAdmin').addEventListener('click', () => {
            this.switchTab('admin');
        });

        // Week start selection
        document.getElementById('weekStart').addEventListener('change', (e) => {
            if (e.target.value) {
                this.generateWeeklyForm(e.target.value);
            } else {
                document.getElementById('weeklyForm').classList.add('hidden');
            }
        });

        // Submit timesheet
        document.getElementById('submitTimesheet').addEventListener('click', () => {
            this.submitTimesheet();
        });

        // Create user
        document.getElementById('createUserBtn').addEventListener('click', () => {
            this.createUser();
        });

        // Save SMTP
        document.getElementById('saveSmtpBtn').addEventListener('click', () => {
            this.saveSmtpConfig();
        });

        // Password change modal
        document.getElementById('changePasswordBtn').addEventListener('click', () => {
            this.showPasswordModal();
        });

        document.getElementById('savePasswordBtn').addEventListener('click', () => {
            this.changePassword();
        });

        document.getElementById('cancelPasswordBtn').addEventListener('click', () => {
            this.hidePasswordModal();
        });

        // Edit user modal
        document.getElementById('saveUserBtn').addEventListener('click', () => {
            this.saveUserEdit();
        });

        document.getElementById('cancelEditUserBtn').addEventListener('click', () => {
            this.hideEditUserModal();
        });
    }

    // Authentication methods
    async handleLogin() {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        this.showLoading(true);
        this.hideMessage('loginError');
        this.hideMessage('loginSuccess');

        try {
            const response = await this.apiCall('POST', 'auth/login', {
                email: email,
                password: password
            });

            if (response.success) {
                this.token = response.data.access_token;
                localStorage.setItem('token', this.token);
                this.currentUser = response.data.user;
                
                this.showMessage('loginSuccess', 'Erfolgreich angemeldet!');
                setTimeout(() => {
                    this.showMainApp();
                }, 1000);
            } else {
                this.showMessage('loginError', response.message || 'Anmeldung fehlgeschlagen');
            }
        } catch (error) {
            this.showMessage('loginError', 'Anmeldung fehlgeschlagen. Bitte überprüfen Sie Ihre Daten.');
        } finally {
            this.showLoading(false);
        }
    }

    async validateToken() {
        try {
            const response = await this.apiCall('GET', 'auth/me');
            if (response.success) {
                this.currentUser = response.data;
                this.showMainApp();
            } else {
                this.handleLogout();
            }
        } catch (error) {
            this.handleLogout();
        }
    }

    handleLogout() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('token');
        this.showLogin();
    }

    // UI Navigation methods
    showLogin() {
        document.getElementById('loginPage').classList.remove('hidden');
        document.getElementById('mainApp').classList.add('hidden');
        this.clearLoginForm();
    }

    showMainApp() {
        document.getElementById('loginPage').classList.add('hidden');
        document.getElementById('mainApp').classList.remove('hidden');
        
        // Set user info
        document.getElementById('userName').textContent = this.currentUser.name;
        if (this.currentUser.is_admin) {
            document.getElementById('adminBadge').classList.remove('hidden');
            document.getElementById('tabAdmin').classList.remove('hidden');
        }

        // Load initial data
        this.switchTab('timesheets');
        this.populateWeekOptions();
    }

    switchTab(tab) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active', 'border-red-500', 'text-red-600');
            btn.classList.add('border-transparent', 'text-gray-500');
        });

        const activeTab = document.getElementById(`tab${tab.charAt(0).toUpperCase() + tab.slice(1)}`);
        activeTab.classList.add('active', 'border-red-500', 'text-red-600');
        activeTab.classList.remove('border-transparent', 'text-gray-500');

        // Show/hide content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });

        const activeContent = document.getElementById(`content${tab.charAt(0).toUpperCase() + tab.slice(1)}`);
        activeContent.classList.remove('hidden');

        this.currentTab = tab;

        // Load tab-specific data
        switch (tab) {
            case 'timesheets':
                this.loadTimesheets();
                break;
            case 'newTimesheet':
                this.resetNewTimesheetForm();
                break;
            case 'admin':
                this.loadUsers();
                this.loadSmtpConfig();
                break;
        }
    }

    // Timesheet methods
    async loadTimesheets() {
        document.getElementById('timesheetsLoading').classList.remove('hidden');
        document.getElementById('timesheetsEmpty').classList.add('hidden');
        document.getElementById('timesheetsTable').classList.add('hidden');

        try {
            const response = await this.apiCall('GET', 'timesheets');
            if (response.success && response.data.length > 0) {
                this.renderTimesheets(response.data);
                document.getElementById('timesheetsTable').classList.remove('hidden');
            } else {
                document.getElementById('timesheetsEmpty').classList.remove('hidden');
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Laden der Stundenzettel');
        } finally {
            document.getElementById('timesheetsLoading').classList.add('hidden');
        }
    }

    renderTimesheets(timesheets) {
        const tbody = document.getElementById('timesheetsTableBody');
        tbody.innerHTML = '';

        timesheets.forEach(timesheet => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${timesheet.week_start} bis ${timesheet.week_end}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${timesheet.user_name}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${this.formatDate(timesheet.created_at)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status-badge ${timesheet.status === 'sent' ? 'status-sent' : 'status-draft'}">
                        ${timesheet.status === 'sent' ? 'Versendet' : 'Entwurf'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div class="flex space-x-2">
                        <button onclick="app.downloadPDF('${timesheet.id}', '${timesheet.user_name}', '${timesheet.week_start}')" 
                                class="action-btn" title="PDF herunterladen">
                            📥
                        </button>
                        <button onclick="app.sendEmail('${timesheet.id}')" 
                                class="action-btn send" title="Per E-Mail senden">
                            📧
                        </button>
                        ${(this.currentUser.is_admin || timesheet.user_id === this.currentUser.id) && timesheet.status === 'draft' ? 
                          `<button onclick="app.deleteTimesheet('${timesheet.id}', '${timesheet.user_name}', '${timesheet.week_start}')" 
                                   class="action-btn delete" title="Löschen">
                               🗑️
                           </button>` : ''}
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    populateWeekOptions() {
        const select = document.getElementById('weekStart');
        const mondays = this.getAvailableMondays();
        
        select.innerHTML = '<option value="">Montag auswählen...</option>';
        
        mondays.forEach(monday => {
            const option = document.createElement('option');
            option.value = monday.value;
            option.textContent = monday.label;
            select.appendChild(option);
        });
    }

    getAvailableMondays() {
        const mondays = [];
        const today = new Date();
        const currentMonday = this.getMonday(today);
        
        // Generate Mondays: from 4 weeks ago to 8 weeks in the future
        for (let i = -4; i <= 8; i++) {
            const monday = new Date(currentMonday.getFullYear(), currentMonday.getMonth(), currentMonday.getDate() + (i * 7));
            const weekNumber = this.getWeekNumber(monday);
            
            mondays.push({
                value: this.formatDateForInput(monday),
                label: `${monday.toLocaleDateString('de-DE')} (KW ${weekNumber})`
            });
        }
        
        return mondays;
    }

    getMonday(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1);
        return new Date(d.getFullYear(), d.getMonth(), diff);
    }

    getWeekNumber(date) {
        const tempDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        tempDate.setDate(tempDate.getDate() + 4 - (tempDate.getDay() || 7));
        const yearStart = new Date(tempDate.getFullYear(), 0, 1);
        return Math.ceil((((tempDate - yearStart) / 86400000) + 1) / 7);
    }

    formatDateForInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    generateWeeklyForm(weekStart) {
        const weekDates = this.getWeekDates(weekStart);
        const weeklyEntries = document.getElementById('weeklyEntries');
        const dayNames = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];
        
        weeklyEntries.innerHTML = '';
        
        weekDates.forEach((date, index) => {
            const dayEntry = document.createElement('div');
            dayEntry.className = 'day-entry';
            dayEntry.innerHTML = `
                <h4>${dayNames[index]} - ${new Date(date).toLocaleDateString('de-DE')}</h4>
                <div class="form-grid">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Startzeit</label>
                        <input type="time" name="start_time_${index}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" placeholder="--:--">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Endzeit</label>
                        <input type="time" name="end_time_${index}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" placeholder="--:--">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Pause (Minuten)</label>
                        <input type="number" name="break_minutes_${index}" value="0" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" placeholder="0">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Ort</label>
                        <input type="text" name="location_${index}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" placeholder="Arbeitsort">
                    </div>
                </div>
                <div class="form-grid-2 mt-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Kunde/Projekt</label>
                        <input type="text" name="customer_project_${index}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" placeholder="Kunde oder Projekt">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Aufgaben</label>
                        <textarea name="tasks_${index}" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500" placeholder="Erledigte Aufgaben"></textarea>
                    </div>
                </div>
                <input type="hidden" name="date_${index}" value="${date}">
            `;
            weeklyEntries.appendChild(dayEntry);
        });
        
        document.getElementById('weeklyForm').classList.remove('hidden');
    }

    getWeekDates(weekStart) {
        const dates = [];
        const startDate = new Date(weekStart);
        
        for (let i = 0; i < 7; i++) {
            const date = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate() + i);
            dates.push(this.formatDateForInput(date));
        }
        
        return dates;
    }

    async submitTimesheet() {
        const weekStart = document.getElementById('weekStart').value;
        if (!weekStart) {
            this.showGlobalMessage('error', 'Bitte wählen Sie einen Wochenbeginn aus.');
            return;
        }

        const entries = [];
        const weeklyEntries = document.getElementById('weeklyEntries');
        
        for (let i = 0; i < 7; i++) {
            const date = weeklyEntries.querySelector(`input[name="date_${i}"]`).value;
            const startTime = weeklyEntries.querySelector(`input[name="start_time_${i}"]`).value;
            const endTime = weeklyEntries.querySelector(`input[name="end_time_${i}"]`).value;
            const breakMinutes = parseInt(weeklyEntries.querySelector(`input[name="break_minutes_${i}"]`).value) || 0;
            const location = weeklyEntries.querySelector(`input[name="location_${i}"]`).value;
            const customerProject = weeklyEntries.querySelector(`input[name="customer_project_${i}"]`).value;
            const tasks = weeklyEntries.querySelector(`textarea[name="tasks_${i}"]`).value;

            entries.push({
                date: date,
                start_time: startTime,
                end_time: endTime,
                break_minutes: breakMinutes,
                location: location,
                customer_project: customerProject,
                tasks: tasks
            });
        }

        this.showLoading(true);

        try {
            const response = await this.apiCall('POST', 'timesheets', {
                week_start: weekStart,
                entries: entries
            });

            if (response.success) {
                this.showGlobalMessage('success', 'Stundenzettel erfolgreich erstellt!');
                this.resetNewTimesheetForm();
                this.switchTab('timesheets');
            } else {
                this.showGlobalMessage('error', response.message || 'Fehler beim Erstellen des Stundenzettels');
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Erstellen des Stundenzettels');
        } finally {
            this.showLoading(false);
        }
    }

    resetNewTimesheetForm() {
        document.getElementById('weekStart').value = '';
        document.getElementById('weeklyForm').classList.add('hidden');
        document.getElementById('weeklyEntries').innerHTML = '';
    }

    // Timesheet actions
    async downloadPDF(timesheetId, userName, weekStart) {
        this.showLoading(true);
        
        try {
            const response = await this.apiCall('POST', `timesheets/${timesheetId}/download-and-email`, {}, 'blob');
            
            if (response instanceof Blob) {
                // Generate filename
                const calendarWeek = this.getWeekNumber(new Date(weekStart));
                const cleanName = userName.replace(/[^\w\-_.]/g, '_').replace(/_+/g, '_');
                const filename = `${cleanName}_KW${calendarWeek.toString().padStart(2, '0')}_001.pdf`;
                
                // Create download link
                const url = window.URL.createObjectURL(response);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
                
                this.showGlobalMessage('success', 'PDF heruntergeladen und Kopie an Admin gesendet!');
                this.loadTimesheets(); // Refresh list
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Herunterladen des PDFs');
        } finally {
            this.showLoading(false);
        }
    }

    async sendEmail(timesheetId) {
        this.showLoading(true);
        
        try {
            const response = await this.apiCall('POST', `timesheets/${timesheetId}/send-email`);
            
            if (response.success) {
                this.showGlobalMessage('success', 'Stundenzettel wurde erfolgreich per E-Mail versendet!');
                this.loadTimesheets(); // Refresh list to show updated status
            } else {
                this.showGlobalMessage('error', response.message || 'Fehler beim Senden der E-Mail');
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Senden der E-Mail. Bitte überprüfen Sie die SMTP-Konfiguration.');
        } finally {
            this.showLoading(false);
        }
    }

    async deleteTimesheet(timesheetId, userName, weekStart) {
        if (!confirm(`Möchten Sie den Stundenzettel von "${userName}" für die Woche ${weekStart} wirklich löschen?`)) {
            return;
        }

        this.showLoading(true);
        
        try {
            const response = await this.apiCall('DELETE', `timesheets/${timesheetId}`);
            
            if (response.success) {
                this.showGlobalMessage('success', 'Stundenzettel erfolgreich gelöscht!');
                this.loadTimesheets(); // Refresh list
            } else {
                this.showGlobalMessage('error', response.message || 'Fehler beim Löschen des Stundenzettels');
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Löschen des Stundenzettels');
        } finally {
            this.showLoading(false);
        }
    }

    // User Management
    async loadUsers() {
        if (!this.currentUser.is_admin) return;

        try {
            const response = await this.apiCall('GET', 'users');
            if (response.success) {
                this.renderUsers(response.data);
                document.getElementById('userCount').textContent = response.data.length;
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Laden der Benutzer');
        }
    }

    renderUsers(users) {
        const usersList = document.getElementById('usersList');
        usersList.innerHTML = '';

        users.forEach(user => {
            const userItem = document.createElement('div');
            userItem.className = 'user-item';
            userItem.innerHTML = `
                <div class="user-info">
                    <h5>${user.name}</h5>
                    <p>${user.email}</p>
                </div>
                <div class="user-actions">
                    ${user.is_admin ? '<span class="admin-badge">Admin</span>' : ''}
                    <button onclick="app.editUser('${user.id}')" class="action-btn" title="Bearbeiten">
                        ✏️
                    </button>
                    <button onclick="app.deleteUser('${user.id}', '${user.name}')" 
                            class="action-btn delete" 
                            title="${user.id === this.currentUser.id ? 'Sie können sich nicht selbst löschen' : 'Benutzer löschen'}"
                            ${user.id === this.currentUser.id ? 'disabled style="opacity: 0.5"' : ''}>
                        🗑️
                    </button>
                </div>
            `;
            usersList.appendChild(userItem);
        });
    }

    async createUser() {
        const email = document.getElementById('newUserEmail').value;
        const name = document.getElementById('newUserName').value;
        const password = document.getElementById('newUserPassword').value;
        const isAdmin = document.getElementById('newUserIsAdmin').checked;

        if (!email || !name || !password) {
            this.showGlobalMessage('error', 'Bitte füllen Sie alle Felder aus.');
            return;
        }

        this.showLoading(true);

        try {
            const response = await this.apiCall('POST', 'auth/register', {
                email: email,
                name: name,
                password: password,
                is_admin: isAdmin
            });

            if (response.success) {
                this.showGlobalMessage('success', 'Benutzer erfolgreich erstellt!');
                this.clearUserForm();
                this.loadUsers();
            } else {
                this.showGlobalMessage('error', response.message || 'Fehler beim Erstellen des Benutzers');
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Erstellen des Benutzers');
        } finally {
            this.showLoading(false);
        }
    }

    editUser(userId) {
        this.editingUserId = userId;
        
        // Find user data
        const usersList = document.getElementById('usersList');
        const userItem = usersList.querySelector(`button[onclick="app.editUser('${userId}')"]`).closest('.user-item');
        const name = userItem.querySelector('h5').textContent;
        const email = userItem.querySelector('p').textContent;
        const isAdmin = userItem.querySelector('.admin-badge') !== null;

        // Populate edit form
        document.getElementById('editUserEmail').value = email;
        document.getElementById('editUserName').value = name;
        document.getElementById('editUserIsAdmin').checked = isAdmin;

        this.showEditUserModal();
    }

    async saveUserEdit() {
        if (!this.editingUserId) return;

        const email = document.getElementById('editUserEmail').value;
        const name = document.getElementById('editUserName').value;
        const isAdmin = document.getElementById('editUserIsAdmin').checked;

        this.showLoading(true);

        try {
            const response = await this.apiCall('PUT', `users/${this.editingUserId}`, {
                email: email,
                name: name,
                is_admin: isAdmin
            });

            if (response.success) {
                this.showGlobalMessage('success', 'Benutzer erfolgreich aktualisiert!');
                this.hideEditUserModal();
                this.loadUsers();
            } else {
                this.showGlobalMessage('error', response.message || 'Fehler beim Aktualisieren des Benutzers');
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Aktualisieren des Benutzers');
        } finally {
            this.showLoading(false);
        }
    }

    async deleteUser(userId, userName) {
        if (userId === this.currentUser.id) {
            this.showGlobalMessage('error', 'Sie können sich nicht selbst löschen.');
            return;
        }

        if (!confirm(`Möchten Sie den Benutzer "${userName}" wirklich löschen? Alle zugehörigen Stundenzettel werden ebenfalls gelöscht.`)) {
            return;
        }

        this.showLoading(true);

        try {
            const response = await this.apiCall('DELETE', `users/${userId}`);
            
            if (response.success) {
                this.showGlobalMessage('success', 'Benutzer erfolgreich gelöscht!');
                this.loadUsers();
            } else {
                this.showGlobalMessage('error', response.message || 'Fehler beim Löschen des Benutzers');
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Löschen des Benutzers');
        } finally {
            this.showLoading(false);
        }
    }

    // SMTP Configuration
    async loadSmtpConfig() {
        if (!this.currentUser.is_admin) return;

        try {
            const response = await this.apiCall('GET', 'admin/smtp-config');
            if (response.success && response.data) {
                document.getElementById('smtpServer').value = response.data.smtp_server || '';
                document.getElementById('smtpPort').value = response.data.smtp_port || 587;
                document.getElementById('smtpUsername').value = response.data.smtp_username || '';
                document.getElementById('adminEmail').value = response.data.admin_email || '';
                // Don't populate password for security
            }
        } catch (error) {
            // SMTP config might not exist yet, that's ok
        }
    }

    async saveSmtpConfig() {
        const smtpServer = document.getElementById('smtpServer').value;
        const smtpPort = parseInt(document.getElementById('smtpPort').value) || 587;
        const smtpUsername = document.getElementById('smtpUsername').value;
        const smtpPassword = document.getElementById('smtpPassword').value;
        const adminEmail = document.getElementById('adminEmail').value;

        if (!smtpServer || !smtpUsername || !adminEmail) {
            this.showGlobalMessage('error', 'Bitte füllen Sie alle SMTP-Felder aus.');
            return;
        }

        this.showLoading(true);

        try {
            const response = await this.apiCall('POST', 'admin/smtp-config', {
                smtp_server: smtpServer,
                smtp_port: smtpPort,
                smtp_username: smtpUsername,
                smtp_password: smtpPassword,
                admin_email: adminEmail
            });

            if (response.success) {
                this.showGlobalMessage('success', 'SMTP-Konfiguration erfolgreich aktualisiert!');
                document.getElementById('smtpPassword').value = ''; // Clear password field
            } else {
                this.showGlobalMessage('error', response.message || 'Fehler beim Aktualisieren der SMTP-Konfiguration');
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Aktualisieren der SMTP-Konfiguration');
        } finally {
            this.showLoading(false);
        }
    }

    // Password change
    async changePassword() {
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (!currentPassword || !newPassword || !confirmPassword) {
            this.showGlobalMessage('error', 'Bitte füllen Sie alle Felder aus.');
            return;
        }

        if (newPassword !== confirmPassword) {
            this.showGlobalMessage('error', 'Die neuen Passwörter stimmen nicht überein.');
            return;
        }

        if (newPassword.length < 6) {
            this.showGlobalMessage('error', 'Das neue Passwort muss mindestens 6 Zeichen lang sein.');
            return;
        }

        this.showLoading(true);

        try {
            const response = await this.apiCall('POST', 'auth/change-password', {
                current_password: currentPassword,
                new_password: newPassword
            });

            if (response.success) {
                this.showGlobalMessage('success', 'Passwort erfolgreich geändert!');
                this.hidePasswordModal();
            } else {
                this.showGlobalMessage('error', response.message || 'Fehler beim Ändern des Passworts');
            }
        } catch (error) {
            this.showGlobalMessage('error', 'Fehler beim Ändern des Passworts');
        } finally {
            this.showLoading(false);
        }
    }

    // Modal methods
    showPasswordModal() {
        document.getElementById('passwordModal').classList.remove('hidden');
        this.clearPasswordForm();
    }

    hidePasswordModal() {
        document.getElementById('passwordModal').classList.add('hidden');
        this.clearPasswordForm();
    }

    showEditUserModal() {
        document.getElementById('editUserModal').classList.remove('hidden');
    }

    hideEditUserModal() {
        document.getElementById('editUserModal').classList.add('hidden');
        this.editingUserId = null;
    }

    // Utility methods
    async apiCall(method, endpoint, data = null, responseType = 'json') {
        const url = `${this.apiBase}/${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);

        if (responseType === 'blob') {
            if (response.ok) {
                return await response.blob();
            } else {
                throw new Error('Request failed');
            }
        }

        const result = await response.json();
        
        if (!response.ok) {
            if (response.status === 401) {
                this.handleLogout();
            }
            throw new Error(result.message || 'Request failed');
        }

        return result;
    }

    showLoading(show) {
        if (show) {
            document.getElementById('loading').classList.remove('hidden');
        } else {
            document.getElementById('loading').classList.add('hidden');
        }
    }

    showMessage(elementId, message) {
        const element = document.getElementById(elementId);
        element.textContent = message;
        element.classList.remove('hidden');
    }

    hideMessage(elementId) {
        const element = document.getElementById(elementId);
        element.classList.add('hidden');
    }

    showGlobalMessage(type, message) {
        const element = document.getElementById('globalMessage');
        element.className = `message ${type}`;
        element.textContent = message;
        element.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            element.classList.add('hidden');
        }, 5000);
    }

    clearLoginForm() {
        document.getElementById('email').value = '';
        document.getElementById('password').value = '';
    }

    clearUserForm() {
        document.getElementById('newUserEmail').value = '';
        document.getElementById('newUserName').value = '';
        document.getElementById('newUserPassword').value = '';
        document.getElementById('newUserIsAdmin').checked = false;
    }

    clearPasswordForm() {
        document.getElementById('currentPassword').value = '';
        document.getElementById('newPassword').value = '';
        document.getElementById('confirmPassword').value = '';
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('de-DE');
    }
}

// Initialize the application
const app = new TimesheetApp();