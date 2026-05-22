/**
 * Prepzo Interview Timer — circular countdown, pause/resume, session timer.
 * Loads settings from GET /api/timer/settings?company_id=&difficulty=
 */
const InterviewTimer = {
  settings: {
    thinking_seconds: 180,
    interview_duration_seconds: 1200,
    reveal_delay_seconds: 0,
    auto_reveal: true,
  },
  questionTotal: 180,
  questionLeft: 180,
  sessionTotal: 1200,
  sessionLeft: 1200,
  questionInterval: null,
  sessionInterval: null,
  paused: false,
  revealed: false,
  questionStartedAt: null,
  onReveal: null,
  onSessionEnd: null,
  circumference: 2 * Math.PI * 54,

  async loadSettings(companyId, difficulty) {
    try {
      const qs = new URLSearchParams();
      if (companyId) qs.set('company_id', companyId);
      if (difficulty) qs.set('difficulty', difficulty);
      const s = await Api.timer.get(qs.toString() ? `?${qs}` : '');
      this.settings = s;
    } catch {
      console.warn('Using default timer settings');
    }
    return this.settings;
  },

  formatTime(sec) {
    const m = Math.floor(Math.max(0, sec) / 60);
    const s = Math.max(0, sec) % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  },

  playEndSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.4);
      setTimeout(() => {
        const o2 = ctx.createOscillator();
        const g2 = ctx.createGain();
        o2.connect(g2);
        g2.connect(ctx.destination);
        o2.frequency.value = 660;
        g2.gain.setValueAtTime(0.12, ctx.currentTime);
        g2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
        o2.start();
        o2.stop(ctx.currentTime + 0.35);
      }, 200);
    } catch {
      /* audio optional */
    }
  },

  updateQuestionRing() {
    const circle = document.getElementById('timer-circle');
    const display = document.getElementById('timer-display');
    const wrap = document.getElementById('timer-ring-wrap');
    if (!circle || !display) return;

    const pct = this.questionTotal > 0 ? this.questionLeft / this.questionTotal : 0;
    circle.style.strokeDashoffset = String(this.circumference * (1 - pct));
    display.textContent = this.formatTime(this.questionLeft);

    wrap?.classList.remove('timer-warning', 'timer-critical', 'timer-done');
    if (this.questionLeft <= 0) wrap?.classList.add('timer-done');
    else if (this.questionLeft <= 10) wrap?.classList.add('timer-critical');
    else if (this.questionLeft <= 30) wrap?.classList.add('timer-warning');
  },

  updateSessionBar() {
    const el = document.getElementById('session-timer-fill');
    const label = document.getElementById('session-timer-label');
    if (!el) return;
    const pct = this.sessionTotal > 0 ? (this.sessionLeft / this.sessionTotal) * 100 : 0;
    el.style.width = `${pct}%`;
    if (label) label.textContent = `Session: ${this.formatTime(this.sessionLeft)}`;
    if (this.sessionLeft <= 60) el.parentElement?.classList.add('session-low');
    else el.parentElement?.classList.remove('session-low');
  },

  startSessionTimer() {
    this.sessionTotal = this.settings.interview_duration_seconds || 1200;
    this.sessionLeft = this.sessionTotal;
    clearInterval(this.sessionInterval);
    this.updateSessionBar();
    this.sessionInterval = setInterval(() => {
      if (this.paused) return;
      this.sessionLeft--;
      this.updateSessionBar();
      if (this.sessionLeft <= 0) {
        clearInterval(this.sessionInterval);
        this.playEndSound();
        if (this.onSessionEnd) this.onSessionEnd();
      }
    }, 1000);
  },

  startQuestionTimer(difficulty) {
    this.revealed = false;
    this.paused = false;
    clearInterval(this.questionInterval);

    return this.loadSettings(
      window.InterviewRoom?.companyId || '',
      difficulty || ''
    ).then(() => {
      this.questionTotal = this.settings.thinking_seconds || 180;
      this.questionLeft = this.questionTotal;
      this.questionStartedAt = Date.now();

      const revealBtn = document.getElementById('reveal-now-btn');
      if (revealBtn) {
        revealBtn.classList.toggle('hidden', this.settings.auto_reveal);
      }

      this.updateQuestionRing();
      this.questionInterval = setInterval(() => this.tickQuestion(), 1000);
    });
  },

  tickQuestion() {
    if (this.paused || this.revealed) return;
    this.questionLeft--;
    this.updateQuestionRing();
    if (this.questionLeft <= 10 && this.questionLeft > 0) {
      document.getElementById('timer-ring-wrap')?.classList.add('timer-pulse');
    }
    if (this.questionLeft <= 0) {
      clearInterval(this.questionInterval);
      document.getElementById('timer-ring-wrap')?.classList.remove('timer-pulse');
      this.playEndSound();
      const delay = (this.settings.reveal_delay_seconds || 0) * 1000;
      if (this.settings.auto_reveal) {
        setTimeout(() => this.triggerReveal(), delay);
      } else {
        document.getElementById('reveal-now-btn')?.classList.remove('hidden');
        Components?.toast('Time is up — reveal answer when ready', 'error');
      }
    }
  },

  triggerReveal() {
    if (this.revealed) return;
    this.revealed = true;
    clearInterval(this.questionInterval);
    if (this.onReveal) this.onReveal();
  },

  pause() {
    this.paused = true;
    document.getElementById('timer-pause-btn')?.classList.add('hidden');
    document.getElementById('timer-resume-btn')?.classList.remove('hidden');
  },

  resume() {
    this.paused = false;
    document.getElementById('timer-pause-btn')?.classList.remove('hidden');
    document.getElementById('timer-resume-btn')?.classList.add('hidden');
  },

  reset() {
    this.questionLeft = this.questionTotal;
    this.revealed = false;
    this.paused = false;
    document.getElementById('timer-pause-btn')?.classList.remove('hidden');
    document.getElementById('timer-resume-btn')?.classList.add('hidden');
    document.getElementById('timer-ring-wrap')?.classList.remove('timer-warning', 'timer-critical', 'timer-done', 'timer-pulse');
    clearInterval(this.questionInterval);
    this.updateQuestionRing();
    this.questionInterval = setInterval(() => this.tickQuestion(), 1000);
    document.getElementById('answer-section')?.classList.add('hidden');
    document.getElementById('timer-section')?.classList.remove('hidden');
  },

  getTimeSpent() {
    if (!this.questionStartedAt) return 0;
    return Math.round((Date.now() - this.questionStartedAt) / 1000);
  },

  getThinkingUsed() {
    return Math.max(0, this.questionTotal - this.questionLeft);
  },

  destroy() {
    clearInterval(this.questionInterval);
    clearInterval(this.sessionInterval);
  },
};
