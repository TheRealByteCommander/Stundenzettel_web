import React, { useState, useEffect } from 'react';
import axios from 'axios';
import DOMPurify from 'dompurify';
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
import { Checkbox } from './components/ui/checkbox';
import { Calendar, Clock, MapPin, User, Building, Send, Download, Plus, Settings, Edit, Trash2, Key, MessageSquare, X, Menu, Home, LogOut, ChevronLeft, Upload, BookOpen } from 'lucide-react';
import { Alert, AlertDescription } from './components/ui/alert';
import { sanitizeHTML, sanitizeInput, validateEmail, validatePassword, validateFilename, escapeHTML, setSecureToken, getSecureToken, clearSecureToken, checkRateLimit } from './utils/security';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://localhost:8000');
const API = `${BACKEND_URL}/api`;

// Axios interceptor for automatic token refresh and error handling
axios.interceptors.request.use(
  (config) => {
    // Add token to every request
    const token = getSecureToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 - token expired or invalid
    if (error.response?.status === 401) {
      clearSecureToken();
      if (typeof window !== 'undefined' && window.location.pathname !== '/') {
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

// Company colors
const colors = {
  primary: '#e90118',    // Rot
  lightGray: '#b3b3b5',  // Hellgrau
  gray: '#5a5a5a'        // Grau
};

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(getSecureToken()); // Use secure token getter
  const [selectedApp, setSelectedApp] = useState(null); // null, 'timesheets', 'expenses'
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [timesheets, setTimesheets] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  // Stats state
  const [statsMonth, setStatsMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  });
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [myRank, setMyRank] = useState(null);
  const [rankTotalUsers, setRankTotalUsers] = useState(null);
  // 2FA state
  const [showOtpDialog, setShowOtpDialog] = useState(false);
  const [show2FASetupDialog, setShow2FASetupDialog] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [tempToken, setTempToken] = useState('');
  const [setupToken, setSetupToken] = useState('');
  const [qrCodeUri, setQrCodeUri] = useState('');

  // New timesheet form
  const [newTimesheet, setNewTimesheet] = useState({
    week_start: '',
    entries: []
  });
  
  // Vacation state
  const [vacationRequests, setVacationRequests] = useState([]);
  const [vacationBalances, setVacationBalances] = useState([]);
  const [vacationRequirements, setVacationRequirements] = useState(null);
  const [currentVacationYear, setCurrentVacationYear] = useState(() => new Date().getFullYear());
  const [newVacationRequest, setNewVacationRequest] = useState({
    start_date: '',
    end_date: '',
    notes: ''
  });
  const [editingBalance, setEditingBalance] = useState(null);
  const [editBalanceDays, setEditBalanceDays] = useState(0);

  // New user form
  const [newUser, setNewUser] = useState({
    email: '',
    name: '',
    password: '',
    role: 'user',  // 'user', 'admin', 'accounting'
    weekly_hours: 40
  });
  
  // Accounting stats
  const [accountingMonth, setAccountingMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  });
  const [accountingStats, setAccountingStats] = useState([]);

  // Push subscription state
  const [pushEnabled, setPushEnabled] = useState(false);

  // SMTP config form
  const [smtpConfig, setSmtpConfig] = useState({
    smtp_server: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    admin_email: ''
  });

  // Announcements
  const [announcements, setAnnouncements] = useState([]);
  const [showAnnouncementDialog, setShowAnnouncementDialog] = useState(false);
  const [editingAnnouncement, setEditingAnnouncement] = useState(null);
  const [announcementForm, setAnnouncementForm] = useState({
    title: '',
    content: '',
    image_url: null,
    image_filename: null,
    active: true
  });

  // Edit user form
  const [editingUser, setEditingUser] = useState(null);
  const [editUserForm, setEditUserForm] = useState({
    email: '',
    name: '',
    role: 'user',
    weekly_hours: 40
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

  // Register Service Worker for PWA
  useEffect(() => {
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
          .then((registration) => {
            console.log('Service Worker registered:', registration);
          })
          .catch((error) => {
            console.log('Service Worker registration failed:', error);
          });
      });
    }
  }, []);

  // Register service worker and subscribe to push after login
  useEffect(() => {
    async function setupPush() {
      try {
        if (!user) return;
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
        const reg = await navigator.serviceWorker.register('/sw.js');
        const perm = await Notification.requestPermission();
        if (perm !== 'granted') { setPushEnabled(false); return; }
        const { data } = await axios.get(`${API}/push/public-key`);
        const vapidKey = data.publicKey;
        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(vapidKey)
        });
        await axios.post(`${API}/push/subscribe`, sub);
        setPushEnabled(true);
      } catch (e) {
        setPushEnabled(false);
      }
    }
    setupPush();
  }, [user]);

  function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  useEffect(() => {
    if (user) {
      fetchTimesheets();
      fetchVacationRequests(currentVacationYear);
      fetchVacationBalance(currentVacationYear);
      fetchVacationRequirements(currentVacationYear);
      if (user.is_admin || user.role === 'admin') {
        fetchUsers();
        fetchSmtpConfig();
      }
      if (user.is_admin || user.role === 'admin' || user.role === 'accounting') {
        fetchAccountingStats(accountingMonth);
      }
      // preload stats for current month
      fetchMonthlyStats(statsMonth);
      fetchMonthlyRank(statsMonth);
    }
    // Always fetch active announcements (even if not logged in fully)
    if (token && user) {
      // For logged in users, fetch active announcements for display
      fetchAnnouncements(true);
      // Fetch available months for expense reports
      if (selectedApp === 'expenses') {
        fetchAvailableMonths();
      }
    } else {
      // For non-logged in users, still fetch active announcements
      fetchAnnouncements(true);
    }
  }, [user, selectedApp]);

  const fetchAnnouncements = async (activeOnly = true) => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const response = await axios.get(`${API}/announcements`, {
        params: { active_only: activeOnly },
        headers
      });
      setAnnouncements(response.data || []);
    } catch (error) {
      console.error('Failed to fetch announcements:', error);
    }
  };

  // Expense Report Functions
  const fetchAvailableMonths = async () => {
    try {
      const response = await axios.get(`${API}/travel-expense-reports/available-months`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAvailableMonths(response.data || []);
    } catch (error) {
      console.error('Failed to fetch available months:', error);
      setAvailableMonths([]);
    }
  };

  const initializeExpenseReport = async (month) => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(
        `${API}/travel-expense-reports/initialize/${month}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCurrentExpenseReport(response.data);
      // Also fetch reports list
      const reportsResponse = await axios.get(`${API}/travel-expense-reports`, {
        params: { month },
        headers: { Authorization: `Bearer ${token}` }
      });
      setExpenseReports(reportsResponse.data || []);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Initialisieren der Abrechnung.');
    } finally {
      setLoading(false);
    }
  };

  const updateExpenseReport = async (reportId, updateData) => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.put(
        `${API}/travel-expense-reports/${reportId}`,
        updateData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCurrentExpenseReport(response.data);
      setSuccess('Abrechnung erfolgreich aktualisiert!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Aktualisieren der Abrechnung.');
    } finally {
      setLoading(false);
    }
  };

  const submitExpenseReport = async (reportId) => {
    setLoading(true);
    setError('');
    try {
      await axios.post(
        `${API}/travel-expense-reports/${reportId}/submit`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess('Abrechnung erfolgreich abgeschlossen und zur Prüfung eingereicht!');
      setTimeout(() => setSuccess(''), 3000);
      // Reload report
      const response = await axios.get(`${API}/travel-expense-reports/${reportId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCurrentExpenseReport(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Abschließen der Abrechnung.');
    } finally {
      setLoading(false);
    }
  };

  const uploadExchangeProof = async (reportId, receiptId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(
      `${API}/travel-expense-reports/${reportId}/receipts/${receiptId}/upload-exchange-proof`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`
        }
      }
    );
    
    return response;
  };

  const uploadReceipt = async (reportId, file) => {
    setLoading(true);
    setError('');
    
    // Security: Validate file
    if (!file) {
      setError('Keine Datei ausgewählt.');
      setLoading(false);
      return;
    }

    // Validate filename
    if (!validateFilename(file.name)) {
      setError('Ungültiger Dateiname. Dateiname darf keine Sonderzeichen oder Pfad-Trenner enthalten.');
      setLoading(false);
      return;
    }

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Nur PDF-Dateien sind erlaubt.');
      setLoading(false);
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Datei ist zu groß. Maximale Größe: 10MB.');
      setLoading(false);
      return;
    }

    // Rate limiting for uploads
    if (!checkRateLimit(10, 60000)) { // Max 10 uploads per minute
      setError('Zu viele Uploads. Bitte versuchen Sie es später erneut.');
      setLoading(false);
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', file);
      await axios.post(
        `${API}/travel-expense-reports/${reportId}/upload-receipt`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      setSuccess('Beleg erfolgreich hochgeladen!');
      setTimeout(() => setSuccess(''), 3000);
      // Reload report
      const response = await axios.get(`${API}/travel-expense-reports/${reportId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCurrentExpenseReport(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Hochladen des Beleges.');
    } finally {
      setLoading(false);
    }
  };

  const deleteReceipt = async (reportId, receiptId) => {
    if (!window.confirm('Möchten Sie diesen Beleg wirklich löschen?')) return;
    setLoading(true);
    setError('');
    try {
      await axios.delete(
        `${API}/travel-expense-reports/${reportId}/receipts/${receiptId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess('Beleg erfolgreich gelöscht!');
      setTimeout(() => setSuccess(''), 3000);
      // Reload report
      const response = await axios.get(`${API}/travel-expense-reports/${reportId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCurrentExpenseReport(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Löschen des Beleges.');
    } finally {
      setLoading(false);
    }
  };

  const fetchChatMessages = async (reportId) => {
    try {
      const response = await axios.get(
        `${API}/travel-expense-reports/${reportId}/chat`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setChatMessages(response.data || []);
    } catch (error) {
      console.error('Failed to fetch chat messages:', error);
      setChatMessages([]);
    }
  };

  const sendChatMessage = async (reportId, message) => {
    if (!message || !message.trim()) return;
    setLoading(true);
    setError('');
    try {
      await axios.post(
        `${API}/travel-expense-reports/${reportId}/chat`,
        `message=${encodeURIComponent(message)}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );
      setNewChatMessage('');
      // Reload chat messages
      await fetchChatMessages(reportId);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Senden der Nachricht.');
    } finally {
      setLoading(false);
    }
  };

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      // Only clear token if it's an authentication error (401)
      if (error.response?.status === 401) {
        clearSecureToken(); // Clear all tokens securely
        setToken(null);
        setUser(null);
      }
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

  const getLast12Months = () => {
    const list = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      list.push({
        value: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
        label: d.toLocaleDateString('de-DE', { year: 'numeric', month: 'long' })
      });
    }
    return list;
  };

  const fetchMonthlyStats = async (month) => {
    try {
      const response = await axios.get(`${API}/stats/monthly`, {
        params: { month },
        headers: { Authorization: `Bearer ${token}` }
      });
      setMonthlyStats(response.data?.stats || []);
    } catch (error) {
      console.error('Failed to fetch monthly stats:', error);
      setMonthlyStats([]);
    }
  };

  const fetchMonthlyRank = async (month) => {
    try {
      const response = await axios.get(`${API}/stats/monthly/rank`, {
        params: { month },
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyRank(response.data?.rank ?? null);
      setRankTotalUsers(response.data?.total_users ?? null);
    } catch (error) {
      console.error('Failed to fetch monthly rank:', error);
      setMyRank(null);
      setRankTotalUsers(null);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Rate limiting check
    if (!checkRateLimit(5, 60000)) { // Max 5 requests per minute
      setError('Zu viele Anmeldeversuche. Bitte versuchen Sie es später erneut.');
      setLoading(false);
      return;
    }

    // Input validation and sanitization
    const sanitizedEmail = sanitizeInput(loginForm.email);
    if (!validateEmail(sanitizedEmail)) {
      setError('Bitte geben Sie eine gültige E-Mail-Adresse ein.');
      setLoading(false);
      return;
    }

    const sanitizedPassword = sanitizeInput(loginForm.password);
    if (sanitizedPassword.length < 8 || sanitizedPassword.length > 128) {
      setError('Ungültiges Passwort.');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: sanitizedEmail,
        password: sanitizedPassword
      });
      if (response.data?.requires_2fa_setup) {
        // User needs to setup 2FA first
        setSetupToken(response.data.setup_token);
        // Fetch QR code
        const qrResponse = await axios.get(`${API}/auth/2fa/setup-qr`, {
          params: { setup_token: response.data.setup_token }
        });
        setQrCodeUri(qrResponse.data.otpauth_uri);
        setShow2FASetupDialog(true);
        setSuccess('Bitte richten Sie 2FA ein, indem Sie den QR-Code mit Google Authenticator scannen.');
        return;
      }
      if (response.data?.requires_2fa) {
        setTempToken(response.data.temp_token);
        setShowOtpDialog(true);
        setSuccess('Bitte geben Sie den 2FA-Code aus Ihrer Authenticator-App ein.');
        return;
      }
      const { access_token, user: userData } = response.data;
      
      // Secure token storage with expiration
      setSecureToken(access_token, 24); // 24 hours expiration
      setToken(access_token);
      setUser(userData);
      setSuccess('Erfolgreich angemeldet!');
    } catch (error) {
      setError('Anmeldung fehlgeschlagen. Bitte überprüfen Sie Ihre Daten.');
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async () => {
    if (!otpCode) return;
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API}/auth/2fa/verify`, { otp: otpCode, temp_token: tempToken });
      const { access_token, user: userData } = response.data;
      setSecureToken(access_token, 24); // Secure token storage
      setToken(access_token);
      setUser(userData);
      setShowOtpDialog(false);
      setOtpCode('');
      setTempToken('');
      setSuccess('2FA erfolgreich verifiziert!');
    } catch (error) {
      setError('Ungültiger 2FA-Code. Bitte erneut versuchen.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearSecureToken(); // Clear all tokens securely
    setToken(null);
    setUser(null);
    setSelectedApp(null);
    setTimesheets([]);
    setUsers([]);
  };

  const getWeekDates = (weekStart) => {
    // Parse date string properly to avoid timezone issues
    const [year, month, day] = weekStart.split('-').map(Number);
    const start = new Date(year, month - 1, day);  // month is 0-indexed
    const dates = [];
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(year, month - 1, day + i);  // Create each date correctly
      dates.push(date.toISOString().split('T')[0]);
    }
    return dates;
  };

  const initializeWeekEntries = (weekStart) => {
    const dates = getWeekDates(weekStart);
    const entries = dates.map(date => ({
      date,
      start_time: '',       // Leer als Default
      end_time: '',         // Leer als Default
      break_minutes: 0,     // 0 als Default
      tasks: '',
      customer_project: '',
      location: '',
      absence_type: null,   // null, "urlaub", "krankheit", "feiertag"
      travel_time_minutes: 0,  // Fahrzeit in Minuten
      include_travel_time: false  // Checkbox "Weiterberechnen"
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

  const uploadSignedTimesheet = async (timesheetId, file) => {
    if (!file) {
      setError('Bitte wählen Sie eine PDF-Datei aus');
      return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Nur PDF-Dateien sind erlaubt');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('Datei zu groß (max 10MB)');
      return;
    }

    // Rate limiting check
    if (!checkRateLimit(5, 60000, 'upload')) {
      setError('Zu viele Uploads in kurzer Zeit. Bitte warten Sie einen Moment.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const token = getSecureToken();
      const response = await axios.post(
        `${API}/timesheets/${timesheetId}/upload-signed`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`
          },
        }
      );
      setSuccess(`Unterschriebener Stundenzettel erfolgreich hochgeladen! ${response.data.accounting_users_notified} Buchhaltungs-User benachrichtigt.`);
      fetchTimesheets(); // Refresh list
    } catch (error) {
      console.error('Upload error:', error);
      setError(error.response?.data?.detail || 'Upload fehlgeschlagen');
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
      // Try to read filename from Content-Disposition header if provided by backend
      let filename = 'stundenzettel.pdf';
      const contentDisposition = response.headers['content-disposition'] || response.headers['Content-Disposition'];
      if (contentDisposition) {
        const match = contentDisposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i);
        if (match) {
          filename = decodeURIComponent(match[1] || match[2]);
        }
      }

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
      setNewUser({ email: '', name: '', password: '', role: 'user', weekly_hours: 40 });
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
  
  const fetchAccountingStats = async (month) => {
    try {
      const response = await axios.get(`${API}/accounting/monthly-stats`, {
        params: { month },
        headers: { Authorization: `Bearer ${token}` }
      });
      setAccountingStats(response.data?.stats || []);
    } catch (error) {
      console.error('Failed to fetch accounting stats:', error);
      setAccountingStats([]);
    }
  };
  
  const downloadAccountingReport = async (month) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/accounting/monthly-report-pdf`, {
        params: { month },
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const monthDate = new Date(`${month}-01`);
      const monthName = monthDate.toLocaleDateString('de-DE', { year: 'numeric', month: '2-digit' });
      link.setAttribute('download', `Buchhaltungsbericht_${monthName}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setSuccess('Buchhaltungsbericht heruntergeladen!');
    } catch (error) {
      setError('Fehler beim Herunterladen des Buchhaltungsberichts.');
    } finally {
      setLoading(false);
    }
  };
  
  const approveTimesheet = async (timesheetId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/timesheets/${timesheetId}/approve`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Stundenzettel erfolgreich genehmigt!');
      fetchTimesheets();
      if (user?.role === 'accounting' || user?.role === 'admin' || user?.is_admin) {
        fetchAccountingStats(accountingMonth);
      }
    } catch (error) {
      setError('Fehler beim Genehmigen des Stundenzettels.');
    } finally {
      setLoading(false);
    }
  };
  
  const rejectTimesheet = async (timesheetId) => {
    if (!confirm('Möchten Sie die Genehmigung für diesen Stundenzettel wirklich zurückziehen?')) {
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API}/timesheets/${timesheetId}/reject`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Genehmigung zurückgezogen!');
      fetchTimesheets();
      if (user?.role === 'accounting' || user?.role === 'admin' || user?.is_admin) {
        fetchAccountingStats(accountingMonth);
      }
    } catch (error) {
      setError('Fehler beim Zurückziehen der Genehmigung.');
    } finally {
      setLoading(false);
    }
  };

  // Freigabe-Bedingung: Button nur aktiv, wenn unterschriebene PDF vorhanden ODER ausschließlich Abwesenheitstage erfasst sind
  const canApproveTimesheet = (timesheet) => {
    try {
      if (timesheet?.signed_pdf_path) return true;
      const entries = Array.isArray(timesheet?.entries) ? timesheet.entries : [];
      if (entries.length === 0) return false;
      const ABSENCE = new Set(['urlaub', 'krankheit', 'feiertag']);
      // Nur Abwesenheit: jeder Eintrag hat Abwesenheitstyp und keine Arbeitszeiten
      const onlyAbsences = entries.every((e) => {
        const absence = e?.absence_type && ABSENCE.has(String(e.absence_type).toLowerCase());
        const hasTimes = Boolean(e?.start_time) || Boolean(e?.end_time);
        return absence && !hasTimes;
      });
      return onlyAbsences;
    } catch (_) {
      return false;
    }
  };

  // Reisekosten: Vorprüfung – für alle Report-Tage muss ein freigegebener, unterschriebener UND verifizierter Stundenzettel existieren
  const isDateInRange = (dateStr, startStr, endStr) => {
    try {
      const d = new Date(dateStr);
      const s = new Date(startStr);
      const e = new Date(endStr);
      if (Number.isNaN(d) || Number.isNaN(s) || Number.isNaN(e)) return false;
      // Inklusive Grenzen
      return d >= s && d <= e;
    } catch (_) {
      return false;
    }
  };

  const hasVerifiedTimesheetForDate = (dateStr) => {
    try {
      return (Array.isArray(timesheets) ? timesheets : []).some((ts) => {
        if (!ts) return false;
        const approved = ts.status === 'approved';
        const signedOk = Boolean(ts.signed_pdf_path) && Boolean(ts.signed_pdf_verified);
        const inWeek = isDateInRange(dateStr, ts.week_start, ts.week_end);
        return approved && signedOk && inWeek;
      });
    } catch (_) {
      return false;
    }
  };

  const getMissingDatesForReport = (report) => {
    try {
      const entries = Array.isArray(report?.entries) ? report.entries : [];
      const dates = entries.map((e) => e?.date).filter(Boolean);
      const uniqueDates = Array.from(new Set(dates));
      return uniqueDates.filter((d) => !hasVerifiedTimesheetForDate(d));
    } catch (_) {
      return [];
    }
  };

  const canSubmitExpenseReport = (report) => {
    const missing = getMissingDatesForReport(report);
    return missing.length === 0;
  };

  const getCoveredAndMissingDates = (report) => {
    const entries = Array.isArray(report?.entries) ? report.entries : [];
    const dates = entries.map((e) => e?.date).filter(Boolean);
    const uniqueDates = Array.from(new Set(dates));
    const missing = uniqueDates.filter((d) => !hasVerifiedTimesheetForDate(d));
    const covered = uniqueDates.filter((d) => hasVerifiedTimesheetForDate(d));
    return { covered, missing };
  };

  // Vacation API functions
  const fetchVacationRequests = async (year) => {
    try {
      const response = await axios.get(`${API}/vacation/requests`, {
        params: year ? { year } : {},
        headers: { Authorization: `Bearer ${token}` }
      });
      setVacationRequests(response.data);
    } catch (error) {
      console.error('Error fetching vacation requests:', error);
    }
  };

  const fetchVacationBalance = async (year) => {
    try {
      const response = await axios.get(`${API}/vacation/balance`, {
        params: year ? { year } : {},
        headers: { Authorization: `Bearer ${token}` }
      });
      setVacationBalances(response.data);
    } catch (error) {
      console.error('Error fetching vacation balance:', error);
    }
  };

  const fetchVacationRequirements = async (year) => {
    try {
      const response = await axios.get(`${API}/vacation/requirements/${year}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVacationRequirements(response.data);
    } catch (error) {
      console.error('Error fetching vacation requirements:', error);
    }
  };

  const createVacationRequest = async () => {
    if (!newVacationRequest.start_date || !newVacationRequest.end_date) {
      setError('Bitte Start- und Enddatum angeben');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await axios.post(`${API}/vacation/requests`, newVacationRequest, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Urlaubsantrag erfolgreich erstellt!');
      setTimeout(() => setSuccess(''), 3000);
      setNewVacationRequest({ start_date: '', end_date: '', notes: '' });
      fetchVacationRequests(currentVacationYear);
      fetchVacationBalance(currentVacationYear);
      fetchVacationRequirements(currentVacationYear);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Erstellen des Urlaubsantrags.');
    } finally {
      setLoading(false);
    }
  };

  const deleteVacationRequest = async (requestId) => {
    if (!confirm('Möchten Sie diesen Urlaubsantrag wirklich löschen?')) {
      return;
    }
    setLoading(true);
    try {
      await axios.delete(`${API}/vacation/requests/${requestId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Urlaubsantrag gelöscht!');
      fetchVacationRequests(currentVacationYear);
      fetchVacationBalance(currentVacationYear);
      fetchVacationRequirements(currentVacationYear);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Löschen.');
    } finally {
      setLoading(false);
    }
  };

  const approveVacationRequest = async (requestId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/vacation/requests/${requestId}/approve`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Urlaubsantrag genehmigt!');
      fetchVacationRequests(currentVacationYear);
      fetchVacationBalance(currentVacationYear);
      fetchVacationRequirements(currentVacationYear);
      fetchTimesheets(); // Refresh timesheets to show new vacation entries
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Genehmigen.');
    } finally {
      setLoading(false);
    }
  };

  const rejectVacationRequest = async (requestId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/vacation/requests/${requestId}/reject`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Urlaubsantrag abgelehnt!');
      fetchVacationRequests(currentVacationYear);
      fetchVacationBalance(currentVacationYear);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Ablehnen.');
    } finally {
      setLoading(false);
    }
  };

  const updateVacationBalance = async (userId, year, totalDays) => {
    setLoading(true);
    try {
      await axios.put(`${API}/vacation/balance/${userId}/${year}`, { total_days: totalDays }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Urlaubstage aktualisiert!');
      fetchVacationBalance(currentVacationYear);
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Aktualisieren.');
    } finally {
      setLoading(false);
    }
  };

  const adminDeleteVacationRequest = async (requestId) => {
    if (!confirm('Möchten Sie diesen genehmigten Urlaubsantrag wirklich löschen? Das Guthaben wird aktualisiert.')) {
      return;
    }
    setLoading(true);
    try {
      await axios.delete(`${API}/vacation/requests/${requestId}/admin-delete`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Urlaubsantrag gelöscht!');
      fetchVacationRequests(currentVacationYear);
      fetchVacationBalance(currentVacationYear);
      fetchVacationRequirements(currentVacationYear);
      fetchTimesheets();
    } catch (error) {
      setError(error.response?.data?.detail || 'Fehler beim Löschen.');
    } finally {
      setLoading(false);
    }
  };

  const editUser = (userItem) => {
    setEditingUser(userItem);
    setEditUserForm({
      email: userItem.email,
      name: userItem.name,
      role: userItem.role || (userItem.is_admin ? 'admin' : 'user'),
      weekly_hours: userItem.weekly_hours || 40
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

  // Helper function to get Monday of the current week (or next Monday if it's Sunday)
  const getMonday = (date) => {
    // Parse date string properly to avoid timezone issues
    let d;
    if (typeof date === 'string') {
      const [year, month, day] = date.split('-').map(Number);
      d = new Date(year, month - 1, day);  // month is 0-indexed
    } else {
      d = new Date(date);
    }
    
    const day = d.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Get Monday of current week
    
    // Create new date with proper timezone handling
    const monday = new Date(d.getFullYear(), d.getMonth(), diff);
    return monday;
  };

  // Helper function to format date for input
  const formatDateForInput = (date) => {
    // Ensure we get local date, not UTC
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Get current Monday and next few Mondays for selection
  const getAvailableMondays = () => {
    const mondays = [];
    const today = new Date();
    const currentMonday = getMonday(today);
    
    // Generate Mondays: from 4 weeks ago to 8 weeks in the future
    for (let i = -4; i <= 8; i++) {
      const monday = new Date(currentMonday.getFullYear(), currentMonday.getMonth(), currentMonday.getDate() + (i * 7));
      
      // Calculate correct calendar week using ISO week calculation
      const tempDate = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate());
      tempDate.setDate(tempDate.getDate() + 4 - (tempDate.getDay() || 7)); // Thursday of this week
      const weekNumber = Math.ceil((((tempDate - new Date(tempDate.getFullYear(), 0, 1)) / 86400000) + 1) / 7);
      
      mondays.push({
        value: formatDateForInput(monday),
        label: `${monday.toLocaleDateString('de-DE')} (KW ${weekNumber})`
      });
    }
    
    return mondays;
  };

  const getDayName = (dateStr) => {
    const days = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
    // Parse date string properly to avoid timezone issues
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day);  // month is 0-indexed
    return days[date.getDay()];
  };

  // Show app selection if logged in but no app selected
  if (token && user && !selectedApp) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center p-4">
        <Card className="w-full max-w-2xl">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center mb-4">
              <Building className="h-8 w-8 mr-2" style={{ color: colors.primary }} />
              <CardTitle className="text-2xl font-bold" style={{ color: colors.gray }}>
                Tick Guard
              </CardTitle>
            </div>
            <CardDescription>Bitte wählen Sie eine Anwendung</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Announcements Display */}
            {announcements.length > 0 && (
              <div className="mb-6 space-y-4">
                {announcements.map((announcement) => (
                  <Card key={announcement.id} className="bg-blue-50 border-blue-200">
                    <CardHeader>
                      <CardTitle className="text-lg">{announcement.title}</CardTitle>
                      {announcement.image_url && (
                        <div className="mt-3">
                          <img 
                            src={announcement.image_url} 
                            alt={announcement.image_filename || 'Ankündigung'} 
                            className="max-w-full h-auto rounded"
                            style={{ maxHeight: '300px' }}
                          />
                        </div>
                      )}
                    </CardHeader>
                    <CardContent>
                      <div 
                        dangerouslySetInnerHTML={{ __html: announcement.content }}
                        className="prose prose-sm max-w-none"
                      />
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* App Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              <Card 
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => setSelectedApp('timesheets')}
              >
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Calendar className="h-6 w-6 mr-2" style={{ color: colors.primary }} />
                    Tick Guard
                  </CardTitle>
                  <CardDescription>
                    Wöchentliche Zeiterfassung und Stundenzettel-Verwaltung
                  </CardDescription>
                </CardHeader>
              </Card>
              
              <Card 
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => setSelectedApp('expenses')}
              >
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <MapPin className="h-6 w-6 mr-2" style={{ color: colors.primary }} />
                    Reisekosten App
                  </CardTitle>
                  <CardDescription>
                    Reisekosten-Erfassung und -Verwaltung
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
            
            <div className="mt-6 flex justify-between items-center">
              {(user?.is_admin || user?.role === 'admin') && (
                <Button 
                  variant="outline"
                  onClick={async () => {
                    // Fetch all announcements for admin
                    await fetchAnnouncements(false);
                    setEditingAnnouncement(null);
                    setAnnouncementForm({
                      title: '',
                      content: '',
                      image_url: null,
                      image_filename: null,
                      active: true
                    });
                    setShowAnnouncementDialog(true);
                  }}
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Ankündigungen verwalten
                </Button>
              )}
              <Button 
                variant="outline"
                onClick={handleLogout}
              >
                Abmelden
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex items-center justify-center mb-4">
              <Building className="h-8 w-8 mr-2" style={{ color: colors.primary }} />
              <CardTitle className="text-2xl font-bold" style={{ color: colors.gray }}>
                Tick Guard
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
                          onChange={(e) => {
                            const sanitized = sanitizeInput(e.target.value);
                            setLoginForm({ ...loginForm, email: sanitized });
                          }}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Passwort</Label>
                <Input
                  id="password"
                  type="password"
                  value={loginForm.password}
                          onChange={(e) => {
                            // Password: Don't sanitize (needs special chars), but limit length
                            const value = e.target.value.slice(0, 128); // Max 128 chars
                            setLoginForm({ ...loginForm, password: value });
                          }}
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
              <p>admin@app.byte-commander.de / admin123</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Mobile Navigation Component
  const MobileNavigation = () => {
    if (!selectedApp) return null;
    
    return (
      <>
        {/* Mobile Menu Button */}
        <button
          className="mobile-menu-button md:hidden"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Menü öffnen"
        >
          <Menu className="h-6 w-6" style={{ color: colors.primary }} />
        </button>

        {/* Mobile Menu Overlay */}
        <div 
          className={`mobile-menu-overlay ${mobileMenuOpen ? 'open' : ''} md:hidden`}
          onClick={() => setMobileMenuOpen(false)}
        />

        {/* Mobile Menu Sidebar */}
        <div className={`mobile-menu ${mobileMenuOpen ? 'open' : ''} md:hidden`}>
          <div className="p-4 border-b flex items-center justify-between">
            <div className="flex items-center">
              <Building className="h-6 w-6 mr-2" style={{ color: colors.primary }} />
              <span className="font-bold" style={{ color: colors.gray }}>Tick Guard</span>
            </div>
            <button onClick={() => setMobileMenuOpen(false)}>
              <X className="h-6 w-6" />
            </button>
          </div>
          
          <div className="p-2">
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <User className="h-5 w-5" style={{ color: colors.gray }} />
                <span className="font-semibold">{user?.name}</span>
              </div>
              {user?.is_admin && (
                <Badge style={{ backgroundColor: colors.primary }}>Admin</Badge>
              )}
              {user?.role === 'accounting' && (
                <Badge style={{ backgroundColor: '#10b981' }}>Buchhaltung</Badge>
              )}
            </div>

            <button
              className="mobile-menu-item w-full text-left"
              onClick={() => {
                window.open('https://github.com/TheRealByteCommander/Stundenzettel_web/blob/main/BENUTZERANLEITUNG.md', '_blank');
                setMobileMenuOpen(false);
              }}
            >
              <BookOpen className="h-5 w-5" />
              <span>Benutzeranleitung</span>
            </button>

            <button
              className="mobile-menu-item w-full text-left"
              onClick={() => {
                setSelectedApp(null);
                setMobileMenuOpen(false);
              }}
            >
              <Home className="h-5 w-5" />
              <span>App-Auswahl</span>
            </button>

            <button
              className="mobile-menu-item w-full text-left"
              onClick={() => {
                setShowPasswordDialog(true);
                setMobileMenuOpen(false);
              }}
            >
              <Key className="h-5 w-5" />
              <span>Passwort ändern</span>
            </button>

            <button
              className="mobile-menu-item w-full text-left"
              onClick={() => {
                handleLogout();
                setMobileMenuOpen(false);
              }}
            >
              <LogOut className="h-5 w-5" />
              <span>Abmelden</span>
            </button>
          </div>
        </div>

        {/* Bottom Navigation (Mobile Only) */}
        {selectedApp === 'timesheets' && (
          <nav className="mobile-nav md:hidden">
            <button
              className={activeTab === 'timesheets' ? 'active' : ''}
              onClick={() => {
                setActiveTab('timesheets');
                document.querySelector('[value="timesheets"]')?.click();
              }}
            >
              <Calendar className="h-5 w-5" />
              <span>Übersicht</span>
            </button>
            <button
              className={activeTab === 'new-timesheet' ? 'active' : ''}
              onClick={() => {
                setActiveTab('new-timesheet');
                document.querySelector('[value="new-timesheet"]')?.click();
              }}
            >
              <Plus className="h-5 w-5" />
              <span>Neu</span>
            </button>
            <button
              className={activeTab === 'stats' ? 'active' : ''}
              onClick={() => {
                setActiveTab('stats');
                document.querySelector('[value="stats"]')?.click();
              }}
            >
              <Building className="h-5 w-5" />
              <span>Statistiken</span>
            </button>
            {(user?.is_admin || user?.role === 'admin') && (
              <button
                className={activeTab === 'admin' ? 'active' : ''}
                onClick={() => {
                  setActiveTab('admin');
                  document.querySelector('[value="admin"]')?.click();
                }}
              >
                <Settings className="h-5 w-5" />
                <span>Admin</span>
              </button>
            )}
          </nav>
        )}

        {selectedApp === 'expenses' && (
          <nav className="mobile-nav md:hidden">
            <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
              <MapPin className="h-5 w-5" />
              <span>Abrechnung</span>
            </button>
            <button onClick={() => {
              if (currentExpenseReport?.id) {
                setShowChatDialog(true);
              }
            }}>
              <MessageSquare className="h-5 w-5" />
              <span>Chat</span>
            </button>
          </nav>
        )}
      </>
    );
  };

  // Show timesheets app
  if (selectedApp === 'timesheets') {
    return (
      <div className="min-h-screen bg-gray-50 content-with-mobile-nav">
        {/* Mobile Navigation */}
        <MobileNavigation />
        
        {/* Header */}
        <header className="bg-white shadow-sm border-b safe-top">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Mobile: Only show logo, Desktop: Full header */}
              <div className="flex items-center">
                <Building className="h-6 w-6 sm:h-8 sm:w-8 mr-2" style={{ color: colors.primary }} />
                <h1 className="text-base sm:text-xl font-bold hidden sm:block" style={{ color: colors.gray }}>
                  Tick Guard GmbH - Zeiterfassung
                </h1>
                <h1 className="text-base font-bold sm:hidden" style={{ color: colors.gray }}>
                  Zeiterfassung
                </h1>
              </div>
              {/* Desktop Header Actions */}
              <div className="hidden md:flex items-center space-x-4">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => window.open('https://github.com/TheRealByteCommander/Stundenzettel_web/blob/main/BENUTZERANLEITUNG.md', '_blank')}
                  title="Benutzeranleitung öffnen"
                >
                  <BookOpen className="h-4 w-4 mr-1" />
                  Anleitung
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setSelectedApp(null)}
                >
                  App wechseln
                </Button>
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4" style={{ color: colors.gray }} />
                  <span style={{ color: colors.gray }}>{user?.name}</span>
                  {user?.is_admin && (
                    <Badge style={{ backgroundColor: colors.primary }}>Admin</Badge>
                  )}
                  {user?.role === 'accounting' && (
                    <Badge style={{ backgroundColor: '#10b981' }}>Buchhaltung</Badge>
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

        <Tabs defaultValue="timesheets" value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Desktop Tabs - Hidden on Mobile (Bottom Nav used instead) */}
          <div className="hidden md:block">
            {user?.is_admin || user?.role === 'admin' ? (
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="timesheets">Stundenzettel</TabsTrigger>
                <TabsTrigger value="new-timesheet">Neuer Stundenzettel</TabsTrigger>
                <TabsTrigger value="vacation">Urlaubsplaner</TabsTrigger>
                <TabsTrigger value="stats">Statistiken</TabsTrigger>
                <TabsTrigger value="admin">Admin</TabsTrigger>
              </TabsList>
            ) : user?.role === 'accounting' ? (
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="timesheets">Alle Stundenzettel</TabsTrigger>
                <TabsTrigger value="vacation">Urlaubsplaner</TabsTrigger>
                <TabsTrigger value="accounting">Buchhaltung</TabsTrigger>
              </TabsList>
            ) : (
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="timesheets">Stundenzettel</TabsTrigger>
                <TabsTrigger value="new-timesheet">Neuer Stundenzettel</TabsTrigger>
                <TabsTrigger value="vacation">Urlaubsplaner</TabsTrigger>
                <TabsTrigger value="stats">Statistiken</TabsTrigger>
              </TabsList>
            )}
          </div>
          
          {/* Mobile Tab Title */}
          <div className="md:hidden mb-4">
            <h2 className="text-xl font-bold" style={{ color: colors.gray }}>
              {activeTab === 'timesheets' && 'Stundenzettel'}
              {activeTab === 'new-timesheet' && 'Neuer Stundenzettel'}
              {activeTab === 'vacation' && 'Urlaubsplaner'}
              {activeTab === 'stats' && 'Statistiken'}
              {activeTab === 'admin' && 'Administration'}
              {activeTab === 'accounting' && 'Buchhaltung'}
            </h2>
          </div>

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
                            <Badge 
                              variant={
                                timesheet.status === 'approved' ? 'default' : 
                                timesheet.status === 'sent' ? 'secondary' : 'outline'
                              }
                              style={
                                timesheet.status === 'approved' ? { backgroundColor: '#10b981' } : {}
                              }
                            >
                              {timesheet.status === 'approved' ? 'Genehmigt' : 
                               timesheet.status === 'sent' ? 'Versendet' : 'Entwurf'}
                            </Badge>
                            {timesheet.signed_pdf_path && (
                              <Badge
                                variant="outline"
                                style={{
                                  marginLeft: 8,
                                  backgroundColor: timesheet.signed_pdf_verified ? '#10b981' : '#f59e0b',
                                  color: 'white'
                                }}
                                title={
                                  timesheet.signed_pdf_verified
                                    ? 'Unterschrift verifiziert'
                                    : 'Unterschrift hochgeladen, Verifikation empfohlen/ausstehend'
                                }
                              >
                                {timesheet.signed_pdf_verified ? 'Unterschrift verifiziert' : 'Unterschrift hochgeladen'}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex space-x-2 flex-wrap gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => downloadPDF(timesheet.id, timesheet.user_name, timesheet.week_start)}
                                title="PDF herunterladen"
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => sendTimesheetEmail(timesheet.id)}
                                style={{ backgroundColor: colors.primary }}
                                disabled={loading || timesheet.status === 'approved'}
                                title={timesheet.status === 'approved' ? 'Stundenzettel bereits genehmigt' : 'Per E-Mail senden'}
                              >
                                <Send className="h-4 w-4" />
                              </Button>
                              {/* Upload unterschriebener Stundenzettel - nur für Owner */}
                              {timesheet.user_id === user?.id && (
                                <label className="cursor-pointer">
                                  <input
                                    type="file"
                                    accept=".pdf"
                                    className="hidden"
                                    onChange={(e) => {
                                      const file = e.target.files?.[0];
                                      if (file) {
                                        uploadSignedTimesheet(timesheet.id, file);
                                        e.target.value = ''; // Reset input
                                      }
                                    }}
                                    disabled={loading}
                                  />
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    asChild
                                    style={{ backgroundColor: timesheet.signed_pdf_path ? '#10b981' : undefined, color: timesheet.signed_pdf_path ? 'white' : undefined }}
                                    title={timesheet.signed_pdf_path ? 'Unterschriebene Version bereits hochgeladen' : 'Unterschriebenen Stundenzettel hochladen'}
                                    disabled={loading}
                                  >
                                    <span>
                                      <Upload className="h-4 w-4" />
                                    </span>
                                  </Button>
                                </label>
                              )}
                              {(user?.role === 'accounting' || user?.role === 'admin' || user?.is_admin) && (
                                <>
                                  {timesheet.status !== 'approved' && (
                                    <Button
                                      size="sm"
                                      onClick={() => approveTimesheet(timesheet.id)}
                                      style={{ backgroundColor: '#10b981' }}
                                      disabled={loading || !canApproveTimesheet(timesheet)}
                                      title={
                                        canApproveTimesheet(timesheet)
                                          ? 'Stundenzettel genehmigen'
                                          : 'Freigabe nur mit unterschriebener PDF oder ausschließlich Abwesenheit'
                                      }
                                    >
                                      ✓ Genehmigen
                                    </Button>
                                  )}
                                  {timesheet.status === 'approved' && (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => rejectTimesheet(timesheet.id)}
                                      disabled={loading}
                                      title="Genehmigung zurückziehen"
                                      className="text-orange-600 hover:text-orange-800"
                                    >
                                      ✗ Ablehnen
                                    </Button>
                                  )}
                                </>
                              )}
                              {((user?.is_admin || user?.role === 'admin') || (timesheet.user_id === user?.id)) && timesheet.status === 'draft' && (
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
                  <Label htmlFor="week-start">Wochenbeginn (nur Montage auswählbar)</Label>
                  <Select
                    value={newTimesheet.week_start}
                    onValueChange={(weekStart) => {
                      setNewTimesheet({ ...newTimesheet, week_start: weekStart });
                      if (weekStart) {
                        initializeWeekEntries(weekStart);
                      }
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Montag auswählen..." />
                    </SelectTrigger>
                    <SelectContent>
                      {getAvailableMondays().map((monday) => (
                        <SelectItem key={monday.value} value={monday.value}>
                          {monday.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {newTimesheet.entries.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold" style={{ color: colors.gray }}>
                      Wöchentliche Zeiterfassung
                    </h3>
                    
                    {newTimesheet.entries.map((entry, index) => {
                      const hasAbsence = entry.absence_type && entry.absence_type !== '';
                      return (
                        <Card key={index} className="p-4">
                          <div className="flex items-center mb-3">
                            <Calendar className="h-4 w-4 mr-2" style={{ color: colors.primary }} />
                            <span className="font-medium" style={{ color: colors.gray }}>
                              {getDayName(entry.date)} - {new Date(entry.date).toLocaleDateString('de-DE')}
                            </span>
                          </div>
                          
                          {/* Abwesenheitstyp Dropdown */}
                          <div className="space-y-2 mb-4">
                            <Label>Abwesenheitstyp</Label>
                            <Select
                              value={entry.absence_type || ''}
                              onValueChange={(value) => updateEntry(index, 'absence_type', value === '' ? null : value)}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Keine Abwesenheit" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="">Keine Abwesenheit</SelectItem>
                                <SelectItem value="urlaub">Urlaub</SelectItem>
                                <SelectItem value="krankheit">Krankheit</SelectItem>
                                <SelectItem value="feiertag">Feiertag</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          
                          {/* Zeiten - nur anzeigen wenn keine Abwesenheit */}
                          {!hasAbsence && (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                              <div className="space-y-2">
                                <Label>Startzeit</Label>
                                <div className="flex items-center">
                                  <Clock className="h-4 w-4 mr-2" style={{ color: colors.gray }} />
                                  <Input
                                    type="time"
                                    value={entry.start_time}
                                    onChange={(e) => updateEntry(index, 'start_time', e.target.value)}
                                    placeholder="--:--"
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
                                    placeholder="--:--"
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
                                  placeholder="0"
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
                          )}
                          
                          {/* Fahrzeit - nur anzeigen wenn keine Abwesenheit */}
                          {!hasAbsence && (
                            <div className="space-y-4 mt-4">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                  <Label>Fahrzeit (Minuten)</Label>
                                  <Input
                                    type="number"
                                    value={entry.travel_time_minutes || 0}
                                    onChange={(e) => updateEntry(index, 'travel_time_minutes', parseInt(e.target.value) || 0)}
                                    min="0"
                                    placeholder="0"
                                  />
                                </div>
                                
                                <div className="space-y-2 flex items-end">
                                  <div className="flex items-center space-x-2">
                                    <Checkbox
                                      id={`include_travel_${index}`}
                                      checked={entry.include_travel_time || false}
                                      onCheckedChange={(checked) => updateEntry(index, 'include_travel_time', checked)}
                                    />
                                    <Label htmlFor={`include_travel_${index}`} className="cursor-pointer">
                                      Weiterberechnen
                                    </Label>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                          
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
                      );
                    })}
                    
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
                      <div className="space-y-2">
                        <Label>Rolle</Label>
                        <Select
                          value={newUser.role}
                          onValueChange={(value) => setNewUser({ ...newUser, role: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="user">Mitarbeiter</SelectItem>
                            <SelectItem value="admin">Administrator</SelectItem>
                            <SelectItem value="accounting">Buchhaltung</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Wochenstundenzahl</Label>
                        <Input
                          type="number"
                          value={newUser.weekly_hours || 40}
                          onChange={(e) => setNewUser({ ...newUser, weekly_hours: parseFloat(e.target.value) || 40 })}
                          min="1"
                          max="60"
                          step="0.5"
                          placeholder="40"
                        />
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
                        {users.map((userItem) => (
                          <div key={userItem.id} className="flex justify-between items-center p-3 bg-gray-50 rounded border">
                            <div>
                              <span className="font-medium">{userItem.name}</span>
                              <br />
                              <span className="text-sm text-gray-500">{userItem.email}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              {userItem.role === 'admin' || userItem.is_admin ? (
                                <Badge style={{ backgroundColor: colors.primary }}>Admin</Badge>
                              ) : null}
                              {userItem.role === 'accounting' && (
                                <Badge style={{ backgroundColor: '#10b981' }}>Buchhaltung</Badge>
                              )}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => editUser(userItem)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => deleteUser(userItem.id, userItem.name)}
                                className="text-red-600 hover:text-red-800"
                                disabled={userItem.id === user?.id} // Prevent self-deletion
                                title={userItem.id === user?.id ? "Sie können sich nicht selbst löschen" : "Benutzer löschen"}
                                style={{ opacity: userItem.id === user?.id ? 0.5 : 1 }}
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

          {/* Stats Tab */}
          <TabsContent value="stats">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Calendar className="h-5 w-5 mr-2" style={{ color: colors.primary }} />
                  Monatsstatistik (versendete Stunden)
                </CardTitle>
                <CardDescription>
                  Übersicht der Gesamtstunden pro Nutzer im ausgewählten Monat
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="max-w-xs">
                  <Label>Monat auswählen</Label>
                  <Select
                    value={statsMonth}
                    onValueChange={(val) => {
                      setStatsMonth(val);
                      fetchMonthlyStats(val);
                      fetchMonthlyRank(val);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Monat auswählen" />
                    </SelectTrigger>
                    <SelectContent>
                      {getLast12Months().map((m) => (
                        <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Rang-Anzeige (keine Offenlegung anderer Zahlen) */}
                {(myRank !== null && rankTotalUsers !== null) && (
                  <div className="p-3 rounded border bg-gray-50">
                    <span className="font-medium" style={{ color: colors.gray }}>
                      Ihre Platzierung: {myRank}. von {rankTotalUsers}
                    </span>
                  </div>
                )}

                {monthlyStats.length === 0 ? (
                  <p style={{ color: colors.gray }}>Keine Daten für diesen Monat vorhanden.</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nutzer</TableHead>
                        <TableHead>Monat</TableHead>
                        <TableHead className="text-right">Gesamtstunden</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {monthlyStats.map((row) => (
                        <TableRow key={row.user_id}>
                          <TableCell>{row.user_name}</TableCell>
                          <TableCell>{row.month}</TableCell>
                          <TableCell className="text-right">{row.total_hours.toFixed(2)} h</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Vacation Planner Tab */}
          <TabsContent value="vacation">
            <div className="space-y-6">
              {/* Year Selector */}
              <Card>
                <CardHeader>
                  <CardTitle>Urlaubsplaner</CardTitle>
                  <CardDescription>
                    Beantragen Sie Ihren Urlaub und verwalten Sie Ihre Urlaubstage
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 mb-4">
                    <Label>Jahr:</Label>
                    <Select
                      value={String(currentVacationYear)}
                      onValueChange={(value) => {
                        const year = parseInt(value);
                        setCurrentVacationYear(year);
                        fetchVacationRequests(year);
                        fetchVacationBalance(year);
                        fetchVacationRequirements(year);
                      }}
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[new Date().getFullYear() - 1, new Date().getFullYear(), new Date().getFullYear() + 1].map(year => (
                          <SelectItem key={year} value={String(year)}>{year}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Vacation Balance */}
                  {vacationBalances.length > 0 && (
                    <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                      {vacationBalances.filter(b => b.year === currentVacationYear).map(balance => (
                        <div key={balance.id} className="flex justify-between items-center">
                          <div>
                            <div className="font-medium">Verfügbare Urlaubstage: {balance.total_days} Tage</div>
                            <div className="text-sm text-gray-600">
                              Genutzt: {balance.used_days} Tage | Verbleibend: {balance.total_days - balance.used_days} Tage
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Requirements Check */}
                  {vacationRequirements && (
                    <div className={`mb-4 p-4 rounded-lg ${vacationRequirements.needs_reminder ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'}`}>
                      <div className="font-medium mb-2">Mindestanforderungen {currentVacationYear}:</div>
                      <ul className="text-sm space-y-1">
                        <li className={vacationRequirements.meets_min_consecutive ? 'text-green-600' : 'text-red-600'}>
                          {vacationRequirements.meets_min_consecutive ? '✓' : '✗'} Mindestens 2 Wochen am Stück (gesetzlicher Erholungsurlaub - BUrlG §7): {vacationRequirements.max_consecutive} Tage
                        </li>
                        <li className={vacationRequirements.meets_min_total ? 'text-green-600' : 'text-red-600'}>
                          {vacationRequirements.meets_min_total ? '✓' : '✗'} Insgesamt mindestens 20 Tage geplant (betriebliche Vorgabe): {vacationRequirements.total_days} Tage
                        </li>
                        <li className={vacationRequirements.meets_deadline ? 'text-green-600' : 'text-red-600'}>
                          {vacationRequirements.meets_deadline ? '✓' : '✗'} Geplant bis 01.02.{currentVacationYear} (betriebliche Vorgabe)
                        </li>
                      </ul>
                      {vacationRequirements.needs_reminder && (
                        <div className="mt-2 text-sm text-orange-600 font-medium">
                          ⚠️ Bitte vervollständigen Sie Ihre Urlaubsplanung!
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
              
              {/* New Vacation Request Form */}
              <Card>
                <CardHeader>
                  <CardTitle>Neuer Urlaubsantrag</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label>Startdatum</Label>
                        <Input
                          type="date"
                          value={newVacationRequest.start_date}
                          onChange={(e) => setNewVacationRequest({ ...newVacationRequest, start_date: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label>Enddatum</Label>
                        <Input
                          type="date"
                          value={newVacationRequest.end_date}
                          onChange={(e) => setNewVacationRequest({ ...newVacationRequest, end_date: e.target.value })}
                        />
                      </div>
                    </div>
                    <div>
                      <Label>Notizen (optional)</Label>
                      <Textarea
                        value={newVacationRequest.notes}
                        onChange={(e) => setNewVacationRequest({ ...newVacationRequest, notes: e.target.value })}
                        placeholder="Zusätzliche Informationen..."
                      />
                    </div>
                    <Button
                      onClick={createVacationRequest}
                      disabled={loading}
                      style={{ backgroundColor: colors.primary }}
                    >
                      Urlaubsantrag stellen
                    </Button>
                  </div>
                </CardContent>
              </Card>
              
              {/* Vacation Requests List */}
              <Card>
                <CardHeader>
                  <CardTitle>Meine Urlaubsanträge</CardTitle>
                </CardHeader>
                <CardContent>
                  {vacationRequests.length === 0 ? (
                    <p className="text-gray-500">Noch keine Urlaubsanträge für {currentVacationYear}</p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Zeitraum</TableHead>
                          <TableHead>Werktage</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Aktionen</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {vacationRequests.filter(req => req.year === currentVacationYear).map((request) => (
                          <TableRow key={request.id}>
                            <TableCell>
                              {request.start_date} bis {request.end_date}
                            </TableCell>
                            <TableCell>{request.working_days} Tage</TableCell>
                            <TableCell>
                              <Badge
                                variant={
                                  request.status === 'approved' ? 'default' :
                                  request.status === 'rejected' ? 'destructive' : 'outline'
                                }
                                style={
                                  request.status === 'approved' ? { backgroundColor: '#10b981' } :
                                  request.status === 'rejected' ? { backgroundColor: '#ef4444' } : {}
                                }
                              >
                                {request.status === 'approved' ? 'Genehmigt' :
                                 request.status === 'rejected' ? 'Abgelehnt' : 'Ausstehend'}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex gap-2">
                                {request.status === 'pending' && request.user_id === user?.id && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => deleteVacationRequest(request.id)}
                                    disabled={loading}
                                    className="text-red-600"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                )}
                                {request.status === 'approved' && (
                                  <span className="text-sm text-gray-500">Nicht mehr änderbar</span>
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
              
              {/* Admin/Accounting: Approval Section */}
              {(user?.role === 'admin' || user?.role === 'accounting' || user?.is_admin) && (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle>Urlaubsanträge zur Genehmigung</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {vacationRequests.filter(req => req.status === 'pending' && req.year === currentVacationYear).length === 0 ? (
                        <p className="text-gray-500">Keine ausstehenden Anträge</p>
                      ) : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Mitarbeiter</TableHead>
                              <TableHead>Zeitraum</TableHead>
                              <TableHead>Werktage</TableHead>
                              <TableHead>Aktionen</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {vacationRequests.filter(req => req.status === 'pending' && req.year === currentVacationYear).map((request) => (
                              <TableRow key={request.id}>
                                <TableCell>{request.user_name}</TableCell>
                                <TableCell>
                                  {request.start_date} bis {request.end_date}
                                </TableCell>
                                <TableCell>{request.working_days} Tage</TableCell>
                                <TableCell>
                                  <div className="flex gap-2">
                                    <Button
                                      size="sm"
                                      onClick={() => approveVacationRequest(request.id)}
                                      disabled={loading}
                                      style={{ backgroundColor: '#10b981' }}
                                    >
                                      ✓ Genehmigen
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => rejectVacationRequest(request.id)}
                                      disabled={loading}
                                      className="text-red-600"
                                    >
                                      ✗ Ablehnen
                                    </Button>
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )}
                    </CardContent>
                  </Card>
                  
                  {/* Admin: All Approved Requests */}
                  {user?.role === 'admin' || user?.is_admin ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>Alle genehmigten Urlaubsanträge</CardTitle>
                      </CardHeader>
                      <CardContent>
                        {vacationRequests.filter(req => req.status === 'approved' && req.year === currentVacationYear).length === 0 ? (
                          <p className="text-gray-500">Keine genehmigten Anträge</p>
                        ) : (
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Mitarbeiter</TableHead>
                                <TableHead>Zeitraum</TableHead>
                                <TableHead>Werktage</TableHead>
                                <TableHead>Aktionen</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {vacationRequests.filter(req => req.status === 'approved' && req.year === currentVacationYear).map((request) => (
                                <TableRow key={request.id}>
                                  <TableCell>{request.user_name}</TableCell>
                                  <TableCell>
                                    {request.start_date} bis {request.end_date}
                                  </TableCell>
                                  <TableCell>{request.working_days} Tage</TableCell>
                                  <TableCell>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => adminDeleteVacationRequest(request.id)}
                                      disabled={loading}
                                      className="text-red-600"
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </Button>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        )}
                      </CardContent>
                    </Card>
                  ) : null}
                  
                  {/* Admin: Vacation Balance Management */}
                  {user?.role === 'admin' || user?.is_admin ? (
                    <Card>
                      <CardHeader>
                        <CardTitle>Urlaubstage verwalten</CardTitle>
                        <CardDescription>
                          Verfügbare Urlaubstage pro Mitarbeiter eintragen (Mo-Fr)
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        {users.length === 0 ? (
                          <p className="text-gray-500">Keine Mitarbeiter gefunden</p>
                        ) : (
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Mitarbeiter</TableHead>
                                <TableHead>Verfügbare Tage</TableHead>
                                <TableHead>Genutzt</TableHead>
                                <TableHead>Verbleibend</TableHead>
                                <TableHead>Aktionen</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {users.map((userItem) => {
                                const balance = vacationBalances.find(b => b.user_id === userItem.id && b.year === currentVacationYear);
                                return (
                                  <TableRow key={userItem.id}>
                                    <TableCell>{userItem.name}</TableCell>
                                    <TableCell>
                                      {balance ? balance.total_days : 'Nicht gesetzt'}
                                    </TableCell>
                                    <TableCell>{balance?.used_days || 0}</TableCell>
                                    <TableCell>
                                      {balance ? balance.total_days - (balance.used_days || 0) : '-'}
                                    </TableCell>
                                    <TableCell>
                                      <Dialog>
                                        <DialogTrigger asChild>
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => {
                                              setEditingBalance(userItem);
                                              setEditBalanceDays(balance?.total_days || 0);
                                            }}
                                          >
                                            Bearbeiten
                                          </Button>
                                        </DialogTrigger>
                                        <DialogContent>
                                          <DialogHeader>
                                            <DialogTitle>Urlaubstage für {userItem.name}</DialogTitle>
                                          </DialogHeader>
                                          <div className="space-y-4">
                                            <div>
                                              <Label>Verfügbare Urlaubstage (Mo-Fr) für {currentVacationYear}</Label>
                                              <Input
                                                type="number"
                                                min="0"
                                                value={editBalanceDays}
                                                onChange={(e) => setEditBalanceDays(parseInt(e.target.value) || 0)}
                                              />
                                            </div>
                                            <Button
                                              onClick={() => {
                                                if (editingBalance) {
                                                  updateVacationBalance(editingBalance.id, currentVacationYear, editBalanceDays);
                                                  setEditingBalance(null);
                                                }
                                              }}
                                              disabled={loading}
                                            >
                                              Speichern
                                            </Button>
                                          </div>
                                        </DialogContent>
                                      </Dialog>
                                    </TableCell>
                                  </TableRow>
                                );
                              })}
                            </TableBody>
                          </Table>
                        )}
                      </CardContent>
                    </Card>
                  ) : null}
                </>
              )}
            </div>
          </TabsContent>
          
          {/* Accounting Tab */}
          {(user?.role === 'accounting' || user?.role === 'admin' || user?.is_admin) && (
            <TabsContent value="accounting">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Calendar className="h-5 w-5 mr-2" style={{ color: colors.primary }} />
                    Buchhaltungsstatistiken
                  </CardTitle>
                  <CardDescription>
                    Detaillierte Monatsstatistiken für die Buchhaltung
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="max-w-xs">
                      <Label>Monat auswählen</Label>
                      <Select
                        value={accountingMonth}
                        onValueChange={(val) => {
                          setAccountingMonth(val);
                          fetchAccountingStats(val);
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Monat auswählen" />
                        </SelectTrigger>
                        <SelectContent>
                          {getLast12Months().map((m) => (
                            <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <Button
                      onClick={() => downloadAccountingReport(accountingMonth)}
                      disabled={loading}
                      style={{ backgroundColor: colors.primary }}
                      className="mt-6"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      PDF Bericht herunterladen
                    </Button>
                  </div>

                  {accountingStats.length === 0 ? (
                    <p style={{ color: colors.gray }}>Keine Daten für diesen Monat vorhanden.</p>
                  ) : (
                    <div className="space-y-4">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Mitarbeiter</TableHead>
                            <TableHead className="text-right">Monatsgesamt-stunden*</TableHead>
                            <TableHead className="text-right">Stunden auf Stundenzetteln</TableHead>
                            <TableHead className="text-right">Fahrzeit gesamt</TableHead>
                            <TableHead className="text-right">Fahrzeit auf Stundenzetteln</TableHead>
                            <TableHead className="text-right">Kilometer</TableHead>
                            <TableHead className="text-right">Reisekosten (€)</TableHead>
                            <TableHead className="text-right">Anzahl Stundenzettel</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {accountingStats.map((stat) => (
                            <TableRow key={stat.user_id}>
                              <TableCell>{stat.user_name}</TableCell>
                              <TableCell className="text-right">{stat.total_hours.toFixed(2)} h</TableCell>
                              <TableCell className="text-right">{stat.hours_on_timesheets.toFixed(2)} h</TableCell>
                              <TableCell className="text-right">{stat.travel_hours.toFixed(2)} h</TableCell>
                              <TableCell className="text-right">{stat.travel_hours_on_timesheets.toFixed(2)} h</TableCell>
                              <TableCell className="text-right">{stat.travel_kilometers > 0 ? stat.travel_kilometers.toFixed(1) + ' km' : '-'}</TableCell>
                              <TableCell className="text-right">{stat.travel_expenses > 0 ? stat.travel_expenses.toFixed(2) + ' €' : '-'}</TableCell>
                              <TableCell className="text-right">{stat.timesheets_count}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      <div className="text-sm" style={{ color: colors.gray }}>
                        <p><b>Erklärung:</b></p>
                        <p>• <b>Monatsgesamtstunden:</b> Alle Stunden inkl. Fahrzeit (wie in Datenbank gespeichert)</p>
                        <p>• <b>Stunden auf Stundenzetteln:</b> Stunden die tatsächlich auf den Stundenzettel-PDFs erscheinen</p>
                        <p>• <b>Fahrzeit gesamt:</b> Gesamte erfasste Fahrzeit (unabhängig von "Weiterberechnen")</p>
                        <p>• <b>Fahrzeit auf Stundenzetteln:</b> Fahrzeit die auf den Stundenzettel-PDFs erscheint (nur wenn "Weiterberechnen" angehakt)</p>
                        <p>• <b>Kilometer:</b> Gesamtkilometer für Reisekosten</p>
                        <p>• <b>Reisekosten:</b> Gesamte Reisekosten in Euro (Spesen, Bahntickets, etc.)</p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
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

      {/* 2FA Setup Dialog */}
      <Dialog open={show2FASetupDialog} onOpenChange={setShow2FASetupDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>2FA Einrichtung (Pflicht)</DialogTitle>
            <DialogDescription>
              Für Ihre Sicherheit ist 2FA obligatorisch. Bitte scannen Sie den QR-Code mit Google Authenticator.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {qrCodeUri && (
              <div className="flex justify-center">
                <img 
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrCodeUri)}`}
                  alt="2FA QR Code"
                  className="border rounded"
                />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="setup-otp-code">2FA Code aus Google Authenticator</Label>
              <Input
                id="setup-otp-code"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/[^0-9]/g, ''))}
                placeholder="000000"
              />
              <p className="text-sm text-gray-600">
                1. Öffnen Sie Google Authenticator auf Ihrem Smartphone<br/>
                2. Scannen Sie den QR-Code oben<br/>
                3. Geben Sie den 6-stelligen Code ein
              </p>
            </div>
            <div className="flex space-x-2">
              <Button 
                onClick={async () => {
                  if (!otpCode || otpCode.length !== 6) {
                    setError('Bitte geben Sie einen 6-stelligen Code ein.');
                    return;
                  }
                  setLoading(true);
                  setError('');
                  try {
                    const response = await axios.post(`${API}/auth/2fa/initial-setup`, {
                      otp: otpCode,
                      temp_token: setupToken
                    });
                    const { access_token, user: userData } = response.data;
                    setSecureToken(access_token, 24); // Secure token storage
                    setToken(access_token);
                    setUser(userData);
                    setShow2FASetupDialog(false);
                    setOtpCode('');
                    setSetupToken('');
                    setQrCodeUri('');
                    setSuccess('2FA erfolgreich eingerichtet!');
                  } catch (error) {
                    setError(error.response?.data?.detail || 'Ungültiger 2FA-Code. Bitte erneut versuchen.');
                  } finally {
                    setLoading(false);
                  }
                }} 
                disabled={loading || !otpCode || otpCode.length !== 6} 
                style={{ backgroundColor: colors.primary }}
              >
                {loading ? 'Richte ein...' : '2FA aktivieren'}
              </Button>
              <Button variant="outline" onClick={() => {
                setShow2FASetupDialog(false);
                setOtpCode('');
                setSetupToken('');
                setQrCodeUri('');
              }}>Abbrechen</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* OTP Dialog */}
      <Dialog open={showOtpDialog} onOpenChange={setShowOtpDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>2FA-Verifizierung</DialogTitle>
            <DialogDescription>
              Bitte geben Sie den 6-stelligen Code aus Ihrer Google Authenticator App ein.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="otp-code">2FA Code</Label>
              <Input
                id="otp-code"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/[^0-9]/g, ''))}
              />
            </div>
            <div className="flex space-x-2">
              <Button onClick={verifyOtp} disabled={loading} style={{ backgroundColor: colors.primary }}>
                {loading ? 'Prüfe...' : 'Bestätigen'}
              </Button>
              <Button variant="outline" onClick={() => setShowOtpDialog(false)}>Abbrechen</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Announcements Management Dialog */}
      <Dialog open={showAnnouncementDialog} onOpenChange={setShowAnnouncementDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Ankündigungen verwalten</DialogTitle>
            <DialogDescription>
              Erstellen und bearbeiten Sie Ankündigungen für die Startseite
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6">
            {/* List of announcements */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold">Bestehende Ankündigungen</h3>
                <Button
                  size="sm"
                  onClick={() => {
                    setEditingAnnouncement(null);
                    setAnnouncementForm({
                      title: '',
                      content: '',
                      image_url: null,
                      image_filename: null,
                      active: true
                    });
                  }}
                  style={{ backgroundColor: colors.primary }}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Neue Ankündigung
                </Button>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {announcements.map((ann) => (
                  <Card key={ann.id} className="p-3">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{ann.title}</span>
                          {ann.active ? (
                            <Badge style={{ backgroundColor: '#10b981' }}>Aktiv</Badge>
                          ) : (
                            <Badge variant="outline">Inaktiv</Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(ann.content, {
                          ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u'],
                          ALLOWED_ATTR: [],
                          ALLOW_DATA_ATTR: false
                        }) }} />
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditingAnnouncement(ann);
                            setAnnouncementForm({
                              title: ann.title,
                              content: ann.content,
                              image_url: ann.image_url,
                              image_filename: ann.image_filename,
                              active: ann.active
                            });
                          }}
                        >
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={async () => {
                            if (window.confirm('Ankündigung wirklich löschen?')) {
                              try {
                                await axios.delete(`${API}/announcements/${ann.id}`, {
                                  headers: { Authorization: `Bearer ${token}` }
                                });
                                await fetchAnnouncements(false); // Fetch all for admin view
                                setSuccess('Ankündigung gelöscht');
                              } catch (error) {
                                setError('Fehler beim Löschen');
                              }
                            }
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
                {announcements.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">Keine Ankündigungen vorhanden</p>
                )}
              </div>
            </div>

            {/* Edit/Create Form */}
            {(editingAnnouncement !== null || (announcementForm.title || announcementForm.content)) && (
              <div className="border-t pt-4 space-y-4">
                <h3 className="font-semibold">
                  {editingAnnouncement ? 'Ankündigung bearbeiten' : 'Neue Ankündigung'}
                </h3>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Titel</Label>
                    <Input
                      value={announcementForm.title}
                      onChange={(e) => {
                        const sanitized = sanitizeInput(e.target.value).slice(0, 200); // Max 200 chars
                        setAnnouncementForm({ ...announcementForm, title: sanitized });
                      }}
                      placeholder="Titel der Ankündigung"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Inhalt (HTML möglich)</Label>
                    <Textarea
                      value={announcementForm.content}
                      onChange={(e) => {
                        // Content can contain HTML, but limit length to prevent abuse
                        const content = e.target.value.slice(0, 10000); // Max 10000 chars
                        setAnnouncementForm({ ...announcementForm, content });
                      }}
                      placeholder="Inhalt der Ankündigung (HTML-Tags möglich, wird beim Speichern sanitized)"
                      className="min-h-[100px]"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Bild (optional)</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="file"
                        accept="image/*"
                        onChange={async (e) => {
                          const file = e.target.files[0];
                          if (file) {
                            setLoading(true);
                            try {
                              const formData = new FormData();
                              formData.append('file', file);
                              const response = await axios.post(`${API}/announcements/upload-image`, formData, {
                                headers: {
                                  Authorization: `Bearer ${token}`,
                                  'Content-Type': 'multipart/form-data'
                                }
                              });
                              setAnnouncementForm({
                                ...announcementForm,
                                image_url: response.data.image_url,
                                image_filename: response.data.image_filename
                              });
                              setSuccess('Bild hochgeladen');
                            } catch (error) {
                              setError('Fehler beim Hochladen des Bildes');
                            } finally {
                              setLoading(false);
                            }
                          }
                        }}
                      />
                      {announcementForm.image_url && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setAnnouncementForm({
                              ...announcementForm,
                              image_url: null,
                              image_filename: null
                            });
                          }}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                    {announcementForm.image_url && (
                      <div className="mt-2">
                        <img 
                          src={announcementForm.image_url} 
                          alt="Preview" 
                          className="max-w-xs h-auto rounded border"
                          style={{ maxHeight: '200px' }}
                        />
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="announcement-active"
                      checked={announcementForm.active}
                      onCheckedChange={(checked) => setAnnouncementForm({ ...announcementForm, active: checked })}
                    />
                    <Label htmlFor="announcement-active" className="cursor-pointer">
                      Ankündigung aktiv
                    </Label>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={async () => {
                        // Input validation
                        const sanitizedTitle = sanitizeInput(announcementForm.title).trim();
                        if (!sanitizedTitle || sanitizedTitle.length < 3 || sanitizedTitle.length > 200) {
                          setError('Titel muss zwischen 3 und 200 Zeichen lang sein');
                          return;
                        }
                        
                        if (!announcementForm.content || announcementForm.content.trim().length < 10) {
                          setError('Inhalt muss mindestens 10 Zeichen lang sein');
                          return;
                        }

                        // Sanitize HTML content before sending (backend will sanitize again)
                        const sanitizedContent = DOMPurify.sanitize(announcementForm.content, {
                          ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a'],
                          ALLOWED_ATTR: ['href', 'title', 'target']
                        });

                        setLoading(true);
                        try {
                          const formData = {
                            title: sanitizedTitle,
                            content: sanitizedContent,
                            image_url: announcementForm.image_url,
                            image_filename: announcementForm.image_filename,
                            active: announcementForm.active
                          };
                          
                          if (editingAnnouncement) {
                            await axios.put(`${API}/announcements/${editingAnnouncement.id}`, formData, {
                              headers: { Authorization: `Bearer ${token}` }
                            });
                            setSuccess('Ankündigung aktualisiert');
                          } else {
                            await axios.post(`${API}/announcements`, formData, {
                              headers: { Authorization: `Bearer ${token}` }
                            });
                            setSuccess('Ankündigung erstellt');
                          }
                          await fetchAnnouncements();
                          setEditingAnnouncement(null);
                          setAnnouncementForm({
                            title: '',
                            content: '',
                            image_url: null,
                            image_filename: null,
                            active: true
                          });
                        } catch (error) {
                          setError(error.response?.data?.detail || 'Fehler beim Speichern');
                        } finally {
                          setLoading(false);
                        }
                      }}
                      disabled={loading}
                      style={{ backgroundColor: colors.primary }}
                    >
                      {loading ? 'Speichere...' : editingAnnouncement ? 'Aktualisieren' : 'Erstellen'}
                    </Button>
                    {editingAnnouncement && (
                      <Button
                        variant="outline"
                        onClick={() => {
                          setEditingAnnouncement(null);
                          setAnnouncementForm({
                            title: '',
                            content: '',
                            image_url: null,
                            image_filename: null,
                            active: true
                          });
                        }}
                      >
                        Abbrechen
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            )}
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
              <div className="space-y-2">
                <Label>Rolle</Label>
                <Select
                  value={editUserForm.role}
                  onValueChange={(value) => setEditUserForm({ ...editUserForm, role: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="user">Mitarbeiter</SelectItem>
                    <SelectItem value="admin">Administrator</SelectItem>
                    <SelectItem value="accounting">Buchhaltung</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Wochenstundenzahl</Label>
                <Input
                  type="number"
                  value={editUserForm.weekly_hours || 40}
                  onChange={(e) => setEditUserForm({ ...editUserForm, weekly_hours: parseFloat(e.target.value) || 40 })}
                  min="1"
                  max="60"
                  step="0.5"
                  placeholder="40"
                />
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

  // Expenses app state
  const [expenseReportMonth, setExpenseReportMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  });
  const [expenseReports, setExpenseReports] = useState([]);
  const [currentExpenseReport, setCurrentExpenseReport] = useState(null);
  const [availableMonths, setAvailableMonths] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [newChatMessage, setNewChatMessage] = useState('');
  const [showChatDialog, setShowChatDialog] = useState(false);
  
  // Mobile Navigation State
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('timesheets');

  // Show expenses app
  if (selectedApp === 'expenses') {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <Building className="h-8 w-8 mr-2" style={{ color: colors.primary }} />
                <h1 className="text-xl font-bold" style={{ color: colors.gray }}>
                  Tick Guard GmbH - Reisekosten
                </h1>
              </div>
              <div className="flex items-center space-x-4">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => window.open('https://github.com/TheRealByteCommander/Stundenzettel_web/blob/main/BENUTZERANLEITUNG.md', '_blank')}
                  title="Benutzeranleitung öffnen"
                >
                  <BookOpen className="h-4 w-4 mr-1" />
                  Anleitung
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setSelectedApp(null)}
                >
                  App wechseln
                </Button>
                <Button variant="outline" onClick={handleLogout}>
                  Abmelden
                </Button>
              </div>
            </div>
          </div>
        </header>
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

          <Card>
            <CardHeader>
              <CardTitle>Reisekostenabrechnung</CardTitle>
              <CardDescription>
                Erstellen Sie eine Reisekostenabrechnung für einen Monat
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Month Selection */}
              <div className="space-y-2">
                <Label>Monat auswählen</Label>
                <Select
                  value={expenseReportMonth}
                  onValueChange={async (month) => {
                    setExpenseReportMonth(month);
                    await initializeExpenseReport(month);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Monat auswählen" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableMonths.map((m) => (
                      <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Current Report */}
              {currentExpenseReport && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-lg font-semibold">Abrechnung für {currentExpenseReport.month}</h3>
                      <Badge 
                        variant={
                          currentExpenseReport.status === 'approved' ? 'default' :
                          currentExpenseReport.status === 'in_review' ? 'secondary' :
                          'outline'
                        }
                        style={
                          currentExpenseReport.status === 'approved' ? { backgroundColor: '#10b981' } :
                          currentExpenseReport.status === 'in_review' ? { backgroundColor: '#f59e0b' } : {}
                        }
                      >
                        {currentExpenseReport.status === 'approved' ? 'Genehmigt' :
                         currentExpenseReport.status === 'in_review' ? 'In Prüfung' :
                         currentExpenseReport.status === 'submitted' ? 'Abgeschlossen' :
                         'Entwurf'}
                      </Badge>
                    </div>
                    {currentExpenseReport.status === 'draft' && (
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          onClick={() => setShowChatDialog(true)}
                        >
                          <MessageSquare className="h-4 w-4 mr-2" />
                          Chat
                        </Button>
                        <Button
                          onClick={async () => {
                            if (window.confirm('Möchten Sie diese Abrechnung wirklich abschließen? Danach können Sie sie nicht mehr bearbeiten.')) {
                              await submitExpenseReport(currentExpenseReport.id);
                            }
                          }}
                          style={{ backgroundColor: colors.primary }}
                          disabled={loading || !canSubmitExpenseReport(currentExpenseReport)}
                          title={
                            canSubmitExpenseReport(currentExpenseReport)
                              ? 'Abrechnung abschließen'
                              : 'Es fehlen verifizierte, unterschriebene Stundenzettel für einige Tage – Reisekosten werden für diese Zeiträume nicht berücksichtigt.'
                          }
                        >
                          Abrechnung abschließen
                        </Button>
                        {!canSubmitExpenseReport(currentExpenseReport) && (
                          <div className="text-sm" style={{ color: '#ef4444' }}>
                            Hinweis: Es fehlen verifizierte, unterschriebene Stundenzettel für folgende Tage:
                            {' '}
                            {getMissingDatesForReport(currentExpenseReport).join(', ')}
                          </div>
                        )}
                      </div>
                    )}
                    {currentExpenseReport.status === 'in_review' && (
                      <Button
                        variant="outline"
                        onClick={() => setShowChatDialog(true)}
                      >
                        <MessageSquare className="h-4 w-4 mr-2" />
                        Chat (Agenten-Rückfragen)
                      </Button>
                    )}
                  </div>

                  {/* Entries from Timesheets - Nur Anzeige, keine Bearbeitung */}
                  <div className="space-y-2">
                    <h4 className="font-medium">Reiseeinträge aus Stundenzetteln (automatisch erstellt)</h4>
                    <p className="text-xs text-gray-500">
                      Diese Einträge werden automatisch aus Ihren genehmigten und unterschriebenen Stundenzetteln erstellt.
                    </p>
                    {/* Übersicht: Abgedeckte vs. fehlende Tage */}
                    {currentExpenseReport && (
                      (() => {
                        const { covered, missing } = getCoveredAndMissingDates(currentExpenseReport);
                        if ((covered.length + missing.length) === 0) return null;
                        return (
                          <div className="grid gap-2" style={{ gridTemplateColumns: '1fr 1fr' }}>
                            <div>
                              <div className="text-sm font-medium" style={{ color: '#10b981' }}>Abgedeckte Tage (verifiziert)</div>
                              <div className="text-sm" style={{ minHeight: 24 }}>
                                {covered.length > 0 ? covered.join(', ') : '—'}
                              </div>
                            </div>
                            <div>
                              <div className="text-sm font-medium" style={{ color: '#ef4444' }}>Fehlende Tage</div>
                              <div className="text-sm" style={{ minHeight: 24 }}>
                                {missing.length > 0 ? missing.join(', ') : '—'}
                              </div>
                            </div>
                          </div>
                        );
                      })()
                    )}
                    {currentExpenseReport.entries && currentExpenseReport.entries.length > 0 ? (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Datum</TableHead>
                            <TableHead>Ort</TableHead>
                            <TableHead>Kunde/Projekt</TableHead>
                            <TableHead>Fahrzeit</TableHead>
                            <TableHead>Arbeitsstunden</TableHead>
                            <TableHead>Tage</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {currentExpenseReport.entries.map((entry, idx) => (
                            <TableRow key={idx}>
                              <TableCell>{new Date(entry.date).toLocaleDateString('de-DE')}</TableCell>
                              <TableCell>{entry.location || '-'}</TableCell>
                              <TableCell>{entry.customer_project || '-'}</TableCell>
                              <TableCell>{entry.travel_time_minutes} Min</TableCell>
                              <TableCell>{entry.working_hours || 0.0} Std</TableCell>
                              <TableCell>{entry.days_count}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    ) : (
                      <p className="text-sm text-gray-500">Keine Einträge aus genehmigten Stundenzetteln gefunden.</p>
                    )}
                  </div>

                  {/* Receipts - Nur Upload, automatische Extraktion */}
                  <div className="space-y-2">
                    <h4 className="font-medium">Belege hochladen</h4>
                    <p className="text-xs text-gray-500 mb-2">
                      Laden Sie einfach Ihre Belege (PDFs) hoch. Alle Daten werden automatisch aus den Dokumenten extrahiert und den Reiseeinträgen zugeordnet.
                    </p>
                    {currentExpenseReport.status === 'draft' && (
                      <div className="mb-4">
                        <Input
                          type="file"
                          accept=".pdf"
                          onChange={async (e) => {
                            const file = e.target.files[0];
                            if (file) {
                              setLoading(true);
                              try {
                                const response = await uploadReceipt(currentExpenseReport.id, file);
                                if (response.data.has_issues) {
                                  alert('Beleg wurde hochgeladen, aber es wurden Probleme festgestellt. Bitte prüfen Sie den Chat.');
                                }
                                // Lade Report neu, um Analysen anzuzeigen
                                await fetchExpenseReport(currentExpenseReport.id);
                              } catch (error) {
                                alert('Fehler beim Hochladen: ' + (error.response?.data?.detail || error.message));
                              } finally {
                                setLoading(false);
                                e.target.value = ''; // Reset file input
                              }
                            }
                          }}
                        />
                        <p className="text-xs text-gray-500 mt-1">Nur PDF-Dateien möglich. Daten werden automatisch extrahiert.</p>
                      </div>
                    )}
                    {currentExpenseReport.receipts && currentExpenseReport.receipts.length > 0 ? (
                      <div className="space-y-2">
                        {currentExpenseReport.receipts.map((receipt) => {
                          // Finde zugehörige Analyse
                          const analysis = currentExpenseReport.document_analyses?.find(
                            a => a.receipt_id === receipt.id
                          )?.analysis;
                          
                          return (
                            <Card key={receipt.id} className="p-3">
                              <div className="flex justify-between items-start">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">{receipt.filename}</span>
                                    <span className="text-sm text-gray-500">
                                      ({Math.round(receipt.file_size / 1024)} KB)
                                    </span>
                                    {analysis && (
                                      <Badge variant={analysis.confidence > 0.7 ? "default" : "secondary"}>
                                        {analysis.document_type === 'hotel_receipt' ? 'Hotel' :
                                         analysis.document_type === 'restaurant_bill' ? 'Restaurant' :
                                         analysis.document_type === 'toll_receipt' ? 'Maut' :
                                         analysis.document_type === 'parking' ? 'Parken' :
                                         analysis.document_type === 'fuel' ? 'Tanken' :
                                         analysis.document_type === 'train_ticket' ? 'Bahn' :
                                         'Sonstiges'}
                                      </Badge>
                                    )}
                                  </div>
                                  {analysis && (
                                    <div className="mt-2 text-sm">
                                      {analysis.extracted_data?.amount && (
                                        <div>
                                          <strong>Betrag:</strong> {analysis.extracted_data.amount} {analysis.extracted_data.currency || 'EUR'}
                                        </div>
                                      )}
                                      {analysis.extracted_data?.date && (
                                        <div>
                                          <strong>Datum:</strong> {new Date(analysis.extracted_data.date).toLocaleDateString('de-DE')}
                                        </div>
                                      )}
                                      {(analysis.validation_issues?.length > 0 || analysis.logic_issues?.length > 0) && (
                                        <div className="mt-2 text-xs" style={{ color: '#ef4444' }}>
                                          <strong>Hinweise:</strong>
                                          <ul className="list-disc list-inside">
                                            {analysis.validation_issues?.map((issue, idx) => (
                                              <li key={idx}>{issue}</li>
                                            ))}
                                            {analysis.logic_issues?.map((issue, idx) => (
                                              <li key={idx}>{issue}</li>
                                            ))}
                                          </ul>
                                        </div>
                                      )}
                                      {/* Fremdwährungs-Nachweis */}
                                      {(receipt.needs_exchange_proof || (analysis.extracted_data?.currency && analysis.extracted_data.currency.toUpperCase() !== 'EUR')) && (
                                        <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                                          <div className="text-xs font-semibold mb-1" style={{ color: '#d97706' }}>
                                            ⚠️ Fremdwährung erkannt ({analysis.extracted_data?.currency || receipt.currency})
                                          </div>
                                          <div className="text-xs mb-2" style={{ color: '#92400e' }}>
                                            Bitte laden Sie einen Nachweis über den tatsächlichen Euro-Betrag hoch (z.B. Kontoauszug).
                                          </div>
                                          {receipt.exchange_proof_filename ? (
                                            <div className="text-xs" style={{ color: '#10b981' }}>
                                              ✅ Nachweis hochgeladen: {receipt.exchange_proof_filename}
                                            </div>
                                          ) : (
                                            currentExpenseReport.status === 'draft' && (
                                              <Input
                                                type="file"
                                                accept=".pdf"
                                                className="text-xs"
                                                onChange={async (e) => {
                                                  const file = e.target.files[0];
                                                  if (file) {
                                                    setLoading(true);
                                                    try {
                                                      await uploadExchangeProof(currentExpenseReport.id, receipt.id, file);
                                                      await fetchExpenseReport(currentExpenseReport.id);
                                                      alert('Nachweis erfolgreich hochgeladen.');
                                                    } catch (error) {
                                                      alert('Fehler beim Hochladen: ' + (error.response?.data?.detail || error.message));
                                                    } finally {
                                                      setLoading(false);
                                                      e.target.value = '';
                                                    }
                                                  }
                                                }}
                                              />
                                            )
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                                {currentExpenseReport.status === 'draft' && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={async () => {
                                      await deleteReceipt(currentExpenseReport.id, receipt.id);
                                    }}
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </Button>
                                )}
                              </div>
                            </Card>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">Noch keine Belege hochgeladen</p>
                    )}
                  </div>

                  {/* Review Notes */}
                  {currentExpenseReport.review_notes && (
                    <Alert>
                      <AlertDescription>
                        <strong>Prüfnotizen:</strong><br/>
                        {currentExpenseReport.review_notes}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* No Report Yet */}
              {!currentExpenseReport && expenseReportMonth && (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">Noch keine Abrechnung für diesen Monat vorhanden</p>
                  <Button
                    onClick={() => initializeExpenseReport(expenseReportMonth)}
                    style={{ backgroundColor: colors.primary }}
                  >
                    Abrechnung initialisieren
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </main>

        {/* Chat Dialog */}
        <Dialog open={showChatDialog} onOpenChange={(open) => {
          setShowChatDialog(open);
          if (open && currentExpenseReport) {
            fetchChatMessages(currentExpenseReport.id);
          }
        }}>
          <DialogContent className="max-w-2xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>Chat mit Agenten</DialogTitle>
              <DialogDescription>
                Klären Sie Rückfragen zur Reisekostenabrechnung
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              {/* Chat Messages */}
              <div className="border rounded-lg p-4 h-96 overflow-y-auto space-y-2">
                {chatMessages.length === 0 && (
                  <p className="text-center text-gray-500 py-8">Noch keine Nachrichten</p>
                )}
                {chatMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`p-2 rounded ${
                      msg.sender === 'user' 
                        ? 'bg-blue-100 ml-8' 
                        : 'bg-gray-100 mr-8'
                    }`}
                  >
                    <div className="text-xs font-medium mb-1">
                      {msg.sender === 'user' ? 'Sie' : 'Agent'}
                    </div>
                    <div>{msg.message}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(msg.created_at).toLocaleString('de-DE')}
                    </div>
                  </div>
                ))}
              </div>

              {/* Send Message */}
              <div className="flex gap-2">
                <Input
                  value={newChatMessage}
                  onChange={(e) => setNewChatMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && newChatMessage.trim()) {
                      sendChatMessage(currentExpenseReport.id, newChatMessage);
                    }
                  }}
                  placeholder="Nachricht eingeben..."
                />
                <Button
                  onClick={() => {
                    if (newChatMessage.trim()) {
                      sendChatMessage(currentExpenseReport.id, newChatMessage);
                    }
                  }}
                  disabled={!newChatMessage.trim()}
                  style={{ backgroundColor: colors.primary }}
                >
                  Senden
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    );
  }

  return null;
}

export default App;