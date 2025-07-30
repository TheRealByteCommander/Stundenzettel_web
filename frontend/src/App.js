import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Badge } from './components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { Calendar, Clock, MapPin, User, Building, Send, Download, Plus, Settings, Edit, Trash2, Key } from 'lucide-react';
import { Alert, AlertDescription } from './components/ui/alert';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Company colors
const colors = {
  primary: '#e90118',    // Rot
  lightGray: '#b3b3b5',  // Hellgrau
  gray: '#5a5a5a'        // Grau
};

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [timesheets, setTimesheets] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // New timesheet form
  const [newTimesheet, setNewTimesheet] = useState({
    week_start: '',
    entries: []
  });

  // New user form
  const [newUser, setNewUser] = useState({
    email: '',
    name: '',
    password: '',
    is_admin: false
  });

  // SMTP config form
  const [smtpConfig, setSmtpConfig] = useState({
    smtp_server: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    admin_email: ''
  });

  // Edit user form
  const [editingUser, setEditingUser] = useState(null);
  const [editUserForm, setEditUserForm] = useState({
    email: '',
    name: '',
    is_admin: false
  });

  // Edit timesheet form
  const [editingTimesheet, setEditingTimesheet] = useState(null);

  // Password change form
  const [passwordChangeForm, setPasswordChangeForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);

  useEffect(() => {
    if (token) {
      fetchUserInfo();
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      fetchTimesheets();
      if (user.is_admin) {
        fetchUsers();
        fetchSmtpConfig();
      }
    }
  }, [user]);

  const fetchUserInfo = async () => {
    try {
      // Mock user info based on token - in real app, decode JWT
      const mockUser = {
        id: '1',
        email: 'admin@schmitz-intralogistik.de',
        name: 'Administrator',
        is_admin: true
      };
      setUser(mockUser);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      localStorage.removeItem('token');
      setToken(null);
    }
  };

  const fetchTimesheets = async () => {
    try {
      const response = await axios.get(`${API}/timesheets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTimesheets(response.data);
    } catch (error) {
      console.error('Failed to fetch timesheets:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const fetchSmtpConfig = async () => {
    try {
      const response = await axios.get(`${API}/admin/smtp-config`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data) {
        setSmtpConfig(prev => ({ ...prev, ...response.data }));
      }
    } catch (error) {
      console.error('Failed to fetch SMTP config:', error);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/login`, loginForm);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      setSuccess('Erfolgreich angemeldet!');
    } catch (error) {
      setError('Anmeldung fehlgeschlagen. Bitte überprüfen Sie Ihre Daten.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setTimesheets([]);
    setUsers([]);
  };

  const getWeekDates = (weekStart) => {
    const start = new Date(weekStart);
    const dates = [];
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(start);
      date.setDate(start.getDate() + i);
      dates.push(date.toISOString().split('T')[0]);
    }
    return dates;
  };

  const initializeWeekEntries = (weekStart) => {
    const dates = getWeekDates(weekStart);
    const entries = dates.map(date => ({
      date,
      start_time: '08:00',
      end_time: '17:00',
      break_minutes: 30,
      tasks: '',
      customer_project: '',
      location: ''
    }));
    
    setNewTimesheet({ week_start: weekStart, entries });
  };

  const updateEntry = (index, field, value) => {
    const updatedEntries = [...newTimesheet.entries];
    updatedEntries[index] = { ...updatedEntries[index], [field]: value };
    setNewTimesheet({ ...newTimesheet, entries: updatedEntries });
  };

  const submitTimesheet = async () => {
    setLoading(true);
    setError('');

    try {
      await axios.post(`${API}/timesheets`, newTimesheet, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Stundenzettel erfolgreich erstellt!');
      setNewTimesheet({ week_start: '', entries: [] });
      fetchTimesheets();
    } catch (error) {
      setError('Fehler beim Erstellen des Stundenzettels.');
    } finally {
      setLoading(false);
    }
  };

  const sendTimesheetEmail = async (timesheetId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/timesheets/${timesheetId}/send-email`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Stundenzettel wurde erfolgreich per E-Mail versendet!');
      fetchTimesheets(); // Refresh to show updated status
    } catch (error) {
      setError('Fehler beim Senden der E-Mail. Bitte überprüfen Sie die SMTP-Konfiguration.');
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async (timesheetId, userName, weekStart) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/timesheets/${timesheetId}/download-and-email`, {}, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      
      // Generate the new filename format: [Name]_[KW]_[Number]
      const getCalendarWeek = (dateStr) => {
        const date = new Date(dateStr);
        const startOfYear = new Date(date.getFullYear(), 0, 1);
        const pastDaysOfYear = (date - startOfYear) / 86400000;
        const weekNumber = Math.ceil((pastDaysOfYear + startOfYear.getDay() + 1) / 7);
        return `KW${weekNumber.toString().padStart(2, '0')}`;
      };
      
      const sanitizeName = (name) => {
        return name.replace(/[^\w\-_.]/g, '_').replace(/_+/g, '_');
      };
      
      const calendarWeek = getCalendarWeek(weekStart);
      const cleanName = sanitizeName(userName);
      // For now, use 001 as sequential number (backend handles the actual counting)
      const filename = `${cleanName}_${calendarWeek}_001.pdf`;
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      setSuccess('PDF heruntergeladen und Kopie an Admin gesendet!');
      fetchTimesheets(); // Refresh to show updated status
    } catch (error) {
      setError('Fehler beim Herunterladen des PDFs.');
    } finally {
      setLoading(false);
    }
  };

  const createUser = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/auth/register`, newUser, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Benutzer erfolgreich erstellt!');
      setNewUser({ email: '', name: '', password: '', is_admin: false });
      fetchUsers();
    } catch (error) {
      setError('Fehler beim Erstellen des Benutzers.');
    } finally {
      setLoading(false);
    }
  };

  const updateSmtpConfig = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/admin/smtp-config`, smtpConfig, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('SMTP-Konfiguration erfolgreich aktualisiert!');
    } catch (error) {
      setError('Fehler beim Aktualisieren der SMTP-Konfiguration.');
    } finally {
      setLoading(false);
    }
  };

  const editUser = (user) => {
    setEditingUser(user);
    setEditUserForm({
      email: user.email,
      name: user.name,
      is_admin: user.is_admin
    });
  };

  const updateUser = async () => {
    setLoading(true);
    try {
      await axios.put(`${API}/users/${editingUser.id}`, editUserForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Benutzer erfolgreich aktualisiert!');
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      setError('Fehler beim Aktualisieren des Benutzers.');
    } finally {
      setLoading(false);
    }
  };

  const deleteUser = async (userId, userName) => {
    if (!confirm(`Möchten Sie den Benutzer "${userName}" wirklich löschen? Alle zugehörigen Stundenzettel werden ebenfalls gelöscht.`)) {
      return;
    }
    
    setLoading(true);
    try {
      await axios.delete(`${API}/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Benutzer erfolgreich gelöscht!');
      fetchUsers(); // Refresh user list immediately
      fetchTimesheets(); // Also refresh timesheets as they might be affected
    } catch (error) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Fehler beim Löschen des Benutzers.');
      }
    } finally {
      setLoading(false);
    }
  };

  const deleteTimesheet = async (timesheetId, userName, weekStart) => {
    if (!confirm(`Möchten Sie den Stundenzettel von "${userName}" für die Woche ${weekStart} wirklich löschen?`)) {
      return;
    }
    
    setLoading(true);
    try {
      await axios.delete(`${API}/timesheets/${timesheetId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Stundenzettel erfolgreich gelöscht!');
      fetchTimesheets(); // Refresh timesheet list immediately
    } catch (error) {
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else {
        setError('Fehler beim Löschen des Stundenzettels.');
      }
    } finally {
      setLoading(false);
    }
  };

  const changePassword = async () => {
    if (passwordChangeForm.new_password !== passwordChangeForm.confirm_password) {
      setError('Die neuen Passwörter stimmen nicht überein.');
      return;
    }

    if (passwordChangeForm.new_password.length < 6) {
      setError('Das neue Passwort muss mindestens 6 Zeichen lang sein.');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/auth/change-password`, {
        current_password: passwordChangeForm.current_password,
        new_password: passwordChangeForm.new_password
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Passwort erfolgreich geändert!');
      setShowPasswordDialog(false);
      setPasswordChangeForm({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      setError('Fehler beim Ändern des Passworts. Überprüfen Sie Ihr aktuelles Passwort.');
    } finally {
      setLoading(false);
    }
  };

  // Helper function to get next Monday from a given date
  const getNextMonday = (date) => {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is sunday
    return new Date(d.setDate(diff));
  };

  // Helper function to format date for input
  const formatDateForInput = (date) => {
    return date.toISOString().split('T')[0];
  };

  // Get current Monday and next few Mondays for selection
  const getAvailableMondays = () => {
    const mondays = [];
    const today = new Date();
    let monday = getNextMonday(today);
    
    // Go back a few weeks to allow past entries
    for (let i = -4; i <= 8; i++) {
      const currentMonday = new Date(monday);
      currentMonday.setDate(monday.getDate() + (i * 7));
      mondays.push({
        value: formatDateForInput(currentMonday),
        label: `${currentMonday.toLocaleDateString('de-DE')} (KW ${Math.ceil(((currentMonday - new Date(currentMonday.getFullYear(), 0, 1)) / 86400000 + 1) / 7)})`
      });
    }
    
    return mondays;
  };

  const getDayName = (dateStr) => {
    const days = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
    const date = new Date(dateStr);
    return days[date.getDay()];
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center mb-4">
              <Building className="h-8 w-8 mr-2" style={{ color: colors.primary }} />
              <CardTitle className="text-2xl font-bold" style={{ color: colors.gray }}>
                Schmitz Intralogistik
              </CardTitle>
            </div>
            <CardDescription>Zeiterfassung System</CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert className="mb-4" variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            {success && (
              <Alert className="mb-4">
                <AlertDescription>{success}</AlertDescription>
              </Alert>
            )}
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">E-Mail</Label>
                <Input
                  id="email"
                  type="email"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Passwort</Label>
                <Input
                  id="password"
                  type="password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                  required
                />
              </div>
              <Button 
                type="submit" 
                className="w-full" 
                disabled={loading}
                style={{ backgroundColor: colors.primary }}
              >
                {loading ? 'Anmelden...' : 'Anmelden'}
              </Button>
            </form>
            <div className="mt-4 text-center text-sm" style={{ color: colors.gray }}>
              <p>Standard Admin:</p>
              <p>admin@schmitz-intralogistik.de / admin123</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Building className="h-8 w-8 mr-2" style={{ color: colors.primary }} />
              <h1 className="text-xl font-bold" style={{ color: colors.gray }}>
                Schmitz Intralogistik GmbH - Zeiterfassung
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4" style={{ color: colors.gray }} />
                <span style={{ color: colors.gray }}>{user?.name}</span>
                {user?.is_admin && (
                  <Badge style={{ backgroundColor: colors.primary }}>Admin</Badge>
                )}
              </div>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setShowPasswordDialog(true)}
              >
                <Key className="h-4 w-4 mr-1" />
                Passwort
              </Button>
              <Button variant="outline" onClick={handleLogout}>
                Abmelden
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <Alert className="mb-6" variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {success && (
          <Alert className="mb-6">
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="timesheets" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="timesheets">Stundenzettel</TabsTrigger>
            <TabsTrigger value="new-timesheet">Neuer Stundenzettel</TabsTrigger>
            {user?.is_admin && <TabsTrigger value="admin">Admin</TabsTrigger>}
          </TabsList>

          {/* Timesheets Tab */}
          <TabsContent value="timesheets">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Calendar className="h-5 w-5 mr-2" style={{ color: colors.primary }} />
                  Meine Stundenzettel
                </CardTitle>
                <CardDescription>
                  Übersicht über alle erstellten Stundenzettel
                </CardDescription>
              </CardHeader>
              <CardContent>
                {timesheets.length === 0 ? (
                  <p style={{ color: colors.gray }}>Keine Stundenzettel vorhanden.</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Zeitraum</TableHead>
                        <TableHead>Mitarbeiter</TableHead>
                        <TableHead>Erstellt am</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Aktionen</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {timesheets.map((timesheet) => (
                        <TableRow key={timesheet.id}>
                          <TableCell>
                            {timesheet.week_start} bis {timesheet.week_end}
                          </TableCell>
                          <TableCell>{timesheet.user_name}</TableCell>
                          <TableCell>
                            {new Date(timesheet.created_at).toLocaleDateString('de-DE')}
                          </TableCell>
                          <TableCell>
                            <Badge variant={timesheet.status === 'sent' ? 'default' : 'secondary'}>
                              {timesheet.status === 'sent' ? 'Versendet' : 'Entwurf'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex space-x-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => downloadPDF(timesheet.id, timesheet.user_name, timesheet.week_start)}
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => sendTimesheetEmail(timesheet.id)}
                                style={{ backgroundColor: colors.primary }}
                                disabled={loading}
                              >
                                <Send className="h-4 w-4" />
                              </Button>
                              {user?.is_admin && timesheet.status === 'draft' && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => deleteTimesheet(timesheet.id, timesheet.user_name, timesheet.week_start)}
                                  className="text-red-600 hover:text-red-800"
                                  title="Nur Entwürfe können gelöscht werden"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* New Timesheet Tab */}
          <TabsContent value="new-timesheet">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Plus className="h-5 w-5 mr-2" style={{ color: colors.primary }} />
                  Neuer Stundenzettel
                </CardTitle>
                <CardDescription>
                  Wöchentlichen Stundenzettel erstellen
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="week-start">Wochenbeginn (Montag)</Label>
                  <Input
                    id="week-start"
                    type="date"
                    value={newTimesheet.week_start}
                    onChange={(e) => {
                      const weekStart = e.target.value;
                      setNewTimesheet({ ...newTimesheet, week_start: weekStart });
                      if (weekStart) {
                        initializeWeekEntries(weekStart);
                      }
                    }}
                  />
                </div>

                {newTimesheet.entries.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold" style={{ color: colors.gray }}>
                      Wöchentliche Zeiterfassung
                    </h3>
                    
                    {newTimesheet.entries.map((entry, index) => (
                      <Card key={index} className="p-4">
                        <div className="flex items-center mb-3">
                          <Calendar className="h-4 w-4 mr-2" style={{ color: colors.primary }} />
                          <span className="font-medium" style={{ color: colors.gray }}>
                            {getDayName(entry.date)} - {new Date(entry.date).toLocaleDateString('de-DE')}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                          <div className="space-y-2">
                            <Label>Startzeit</Label>
                            <div className="flex items-center">
                              <Clock className="h-4 w-4 mr-2" style={{ color: colors.gray }} />
                              <Input
                                type="time"
                                value={entry.start_time}
                                onChange={(e) => updateEntry(index, 'start_time', e.target.value)}
                              />
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Endzeit</Label>
                            <div className="flex items-center">
                              <Clock className="h-4 w-4 mr-2" style={{ color: colors.gray }} />
                              <Input
                                type="time"
                                value={entry.end_time}
                                onChange={(e) => updateEntry(index, 'end_time', e.target.value)}
                              />
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Pause (Minuten)</Label>
                            <Input
                              type="number"
                              value={entry.break_minutes}
                              onChange={(e) => updateEntry(index, 'break_minutes', parseInt(e.target.value) || 0)}
                              min="0"
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Ort</Label>
                            <div className="flex items-center">
                              <MapPin className="h-4 w-4 mr-2" style={{ color: colors.gray }} />
                              <Input
                                value={entry.location}
                                onChange={(e) => updateEntry(index, 'location', e.target.value)}
                                placeholder="Arbeitsort"
                              />
                            </div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                          <div className="space-y-2">
                            <Label>Kunde/Projekt</Label>
                            <Input
                              value={entry.customer_project}
                              onChange={(e) => updateEntry(index, 'customer_project', e.target.value)}
                              placeholder="Kunde oder Projekt"
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <Label>Aufgaben</Label>
                            <Textarea
                              value={entry.tasks}
                              onChange={(e) => updateEntry(index, 'tasks', e.target.value)}
                              placeholder="Erledigte Aufgaben"
                              className="h-20"
                            />
                          </div>
                        </div>
                      </Card>
                    ))}
                    
                    <Button
                      onClick={submitTimesheet}
                      disabled={loading}
                      className="w-full mt-6"
                      style={{ backgroundColor: colors.primary }}
                    >
                      {loading ? 'Erstelle...' : 'Stundenzettel erstellen'}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Admin Tab */}
          {user?.is_admin && (
            <TabsContent value="admin">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* User Management */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <User className="h-5 w-5 mr-2" style={{ color: colors.primary }} />
                      Benutzerverwaltung
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <Input
                        placeholder="E-Mail"
                        value={newUser.email}
                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                      />
                      <Input
                        placeholder="Name"
                        value={newUser.name}
                        onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                      />
                      <Input
                        type="password"
                        placeholder="Passwort"
                        value={newUser.password}
                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                      />
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="is-admin"
                          checked={newUser.is_admin}
                          onChange={(e) => setNewUser({ ...newUser, is_admin: e.target.checked })}
                        />
                        <Label htmlFor="is-admin">Administrator</Label>
                      </div>
                      <Button
                        onClick={createUser}
                        disabled={loading}
                        style={{ backgroundColor: colors.primary }}
                      >
                        Benutzer erstellen
                      </Button>
                    </div>
                    
                    <div className="mt-6">
                      <h4 className="font-medium mb-3" style={{ color: colors.gray }}>
                        Benutzer ({users.length})
                      </h4>
                      <div className="space-y-2">
                        {users.map((user) => (
                          <div key={user.id} className="flex justify-between items-center p-3 bg-gray-50 rounded border">
                            <div>
                              <span className="font-medium">{user.name}</span>
                              <br />
                              <span className="text-sm text-gray-500">{user.email}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              {user.is_admin && (
                                <Badge style={{ backgroundColor: colors.primary }}>Admin</Badge>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => editUser(user)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => deleteUser(user.id, user.name)}
                                className="text-red-600 hover:text-red-800"
                                disabled={user.id === user?.id} // Prevent self-deletion
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* SMTP Configuration */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Settings className="h-5 w-5 mr-2" style={{ color: colors.primary }} />
                      SMTP Konfiguration
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Input
                      placeholder="SMTP Server"
                      value={smtpConfig.smtp_server}
                      onChange={(e) => setSmtpConfig({ ...smtpConfig, smtp_server: e.target.value })}
                    />
                    <Input
                      type="number"
                      placeholder="SMTP Port"
                      value={smtpConfig.smtp_port}
                      onChange={(e) => setSmtpConfig({ ...smtpConfig, smtp_port: parseInt(e.target.value) || 587 })}
                    />
                    <Input
                      placeholder="SMTP Benutzername"
                      value={smtpConfig.smtp_username}
                      onChange={(e) => setSmtpConfig({ ...smtpConfig, smtp_username: e.target.value })}
                    />
                    <Input
                      type="password"
                      placeholder="SMTP Passwort"
                      value={smtpConfig.smtp_password}
                      onChange={(e) => setSmtpConfig({ ...smtpConfig, smtp_password: e.target.value })}
                    />
                    <Input
                      placeholder="Admin E-Mail"
                      value={smtpConfig.admin_email}
                      onChange={(e) => setSmtpConfig({ ...smtpConfig, admin_email: e.target.value })}
                    />
                    <Button
                      onClick={updateSmtpConfig}
                      disabled={loading}
                      style={{ backgroundColor: colors.primary }}
                    >
                      SMTP Konfiguration speichern
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          )}
        </Tabs>
      </main>

      {/* Password Change Dialog */}
      <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Passwort ändern</DialogTitle>
            <DialogDescription>
              Geben Sie Ihr aktuelles und neues Passwort ein.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">Aktuelles Passwort</Label>
              <Input
                id="current-password"
                type="password"
                value={passwordChangeForm.current_password}
                onChange={(e) => setPasswordChangeForm({ ...passwordChangeForm, current_password: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">Neues Passwort</Label>
              <Input
                id="new-password"
                type="password"
                value={passwordChangeForm.new_password}
                onChange={(e) => setPasswordChangeForm({ ...passwordChangeForm, new_password: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Neues Passwort bestätigen</Label>
              <Input
                id="confirm-password"
                type="password"
                value={passwordChangeForm.confirm_password}
                onChange={(e) => setPasswordChangeForm({ ...passwordChangeForm, confirm_password: e.target.value })}
              />
            </div>
            <div className="flex space-x-2">
              <Button
                onClick={changePassword}
                disabled={loading}
                style={{ backgroundColor: colors.primary }}
              >
                {loading ? 'Ändere...' : 'Passwort ändern'}
              </Button>
              <Button variant="outline" onClick={() => setShowPasswordDialog(false)}>
                Abbrechen
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      {editingUser && (
        <Dialog open={!!editingUser} onOpenChange={() => setEditingUser(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Benutzer bearbeiten</DialogTitle>
              <DialogDescription>
                Bearbeiten Sie die Benutzerdaten von {editingUser.name}.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="edit-email">E-Mail</Label>
                <Input
                  id="edit-email"
                  type="email"
                  value={editUserForm.email}
                  onChange={(e) => setEditUserForm({ ...editUserForm, email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-name">Name</Label>
                <Input
                  id="edit-name"
                  value={editUserForm.name}
                  onChange={(e) => setEditUserForm({ ...editUserForm, name: e.target.value })}
                />
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="edit-is-admin"
                  checked={editUserForm.is_admin}
                  onChange={(e) => setEditUserForm({ ...editUserForm, is_admin: e.target.checked })}
                />
                <Label htmlFor="edit-is-admin">Administrator</Label>
              </div>
              <div className="flex space-x-2">
                <Button
                  onClick={updateUser}
                  disabled={loading}
                  style={{ backgroundColor: colors.primary }}
                >
                  {loading ? 'Speichere...' : 'Speichern'}
                </Button>
                <Button variant="outline" onClick={() => setEditingUser(null)}>
                  Abbrechen
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

export default App;