/**
 * Prepzo Interview Timer — mandatory prep (45s), answer timer by difficulty, 30min quiz cap.
 * Phases: prep → answer → (submit reveals ideal answer)
 */
const InterviewTimer = {
  settings: {
    prep_seconds: 45,
    answer_seconds: 90,
    quiz_max_seconds: 1800,
    auto_next_on_timeout: true,
    answer_by_difficulty: { Easy: 45, Medium: 90, Hard: 120 },
  },
  phase: 'idle', // prep | answer
  practiceWithoutTimer: false,
  prepTotal: 45,
  prepLeft: 45,
  answerTotal: 90,
  answerLeft: 90,
  quizTotal: 1800,
  quizLeft: 1800,
  prepInterval: null,
  answerInterval: null,
  quizInterval: null,
  questionStartedAt: null,
  prepUsed: 0,
  answerUsed: 0,
  circumference: 2 * Math.PI * 54,
  onPrepEnd: null,
  onAnswerEnd: null,
  onQuizEnd: null,

  async loadSettings(companyId, difficulty) {
    try {
      const qs = new URLSearchParams();
      if (companyId) qs.set('company_id', companyId);
      if (difficulty) qs.set('difficulty', difficulty);
      const s = await Api.timer.get(qs.toString() ? `?${qs}` : '');
      this.settings = { ...this.settings, ...s };
    } catch (e) {
      console.warn('[Prepzo Timer] Using defaults', e.message);
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
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.35);
    } catch {
      /* optional */
    }
  },

  _setPhaseLabel(text, sub) {
    const label = document.getElementById('phase-label');
    const subEl = document.getElementById('phase-sublabel');
    if (label) label.textContent = text;
    if (subEl) subEl.textContent = sub || '';
  },

  _updateRing(left, total, subText) {
    const circle = document.getElementById('timer-circle');
    const display = document.getElementById('timer-display');
    const wrap = document.getElementById('timer-ring-wrap');
    const bar = document.getElementById('phase-progress-fill');
    if (!circle || !display) return;

    const pct = total > 0 ? left / total : 0;
    circle.style.strokeDashoffset = String(this.circumference * (1 - pct));
    display.textContent = this.formatTime(left);
    if (bar) bar.style.width = `${pct * 100}%`;

    const sub = document.querySelector('.timer-display-sub');
    if (sub && subText) sub.textContent = subText;

    wrap?.classList.remove('timer-warning', 'timer-critical', 'timer-done', 'timer-pulse');
    if (left <= 0) wrap?.classList.add('timer-done');
    else if (left <= 10) {
      wrap?.classList.add('timer-critical', 'timer-pulse');
    } else if (left <= 20) wrap?.classList.add('timer-warning');
  },

  _updateQuizBar() {
    const el = document.getElementById('session-timer-fill');
    const label = document.getElementById('session-timer-label');
    if (!el) return;
    const pct = this.quizTotal > 0 ? (this.quizLeft / this.quizTotal) * 100 : 0;
    el.style.width = `${pct}%`;
    if (label) label.textContent = `Quiz: ${this.formatTime(this.quizLeft)} / ${this.formatTime(this.quizTotal)}`;
    el.parentElement?.classList.toggle('session-low', this.quizLeft <= 120);
  },

  startQuizTimer() {
    this.quizTotal = this.settings.quiz_max_seconds || 1800;
    this.quizLeft = this.quizTotal;
    clearInterval(this.quizInterval);
    this._updateQuizBar();
    this.quizInterval = setInterval(() => {
      this.quizLeft--;
      this._updateQuizBar();
      if (this.quizLeft <= 0) {
        clearInterval(this.quizInterval);
        this.playEndSound();
        if (this.onQuizEnd) this.onQuizEnd();
      }
    }, 1000);
  },

  stopAll() {
    clearInterval(this.prepInterval);
    clearInterval(this.answerInterval);
  },

  async startQuestion(companyId, difficulty) {
    this.stopAll();
    this.phase = 'prep';
    this.questionStartedAt = Date.now();
    this.prepUsed = 0;
    this.answerUsed = 0;

    await this.loadSettings(companyId, difficulty);

    const byDiff = this.settings.answer_by_difficulty || {};
    this.prepTotal = this.settings.prep_seconds || 45;
    this.prepLeft = this.prepTotal;
    this.answerTotal =
      byDiff[difficulty] || this.settings.answer_seconds || byDiff.Medium || 90;

    this._setPhaseLabel('Preparation', 'Read the question — answer field unlocks when prep ends');
    document.getElementById('timer-section')?.classList.remove('hidden');
    document.getElementById('answer-input-section')?.classList.add('hidden');
    document.getElementById('feedback-section')?.classList.add('hidden');

    this._updateRing(this.prepLeft, this.prepTotal, 'Prep time (required)');

    this.prepInterval = setInterval(() => this._tickPrep(), 1000);
  },

  _tickPrep() {
    this.prepLeft--;
    this.prepUsed = this.prepTotal - this.prepLeft;
    this._updateRing(this.prepLeft, this.prepTotal, 'Prep time (required)');

    if (this.prepLeft <= 0) {
      clearInterval(this.prepInterval);
      this.playEndSound();
      this.startAnswerPhase();
    }
  },

  startAnswerPhase() {
    this.phase = 'answer';
    const untimed = this.practiceWithoutTimer;
    if (this.onPrepEnd) this.onPrepEnd();

    document.getElementById('answer-input-section')?.classList.remove('hidden');
    document.getElementById('user-answer')?.focus();

    if (untimed) {
      this._setPhaseLabel('Answer', 'Practice mode — no answer timer (prep was required)');
      document.getElementById('timer-display').textContent = '∞';
      document.getElementById('phase-progress-fill')?.style.setProperty('width', '100%');
      document.querySelector('.timer-display-sub').textContent = 'Untimed practice';
      document.getElementById('timer-ring-wrap')?.classList.remove('timer-warning', 'timer-critical');
      return;
    }

    this.answerLeft = this.answerTotal;
    this._setPhaseLabel('Answer', `${this.answerTotal}s to respond — auto-advance when time ends`);
    this._updateRing(this.answerLeft, this.answerTotal, 'Answer time');

    clearInterval(this.answerInterval);
    this.answerInterval = setInterval(() => this._tickAnswer(), 1000);
  },

  _tickAnswer() {
    this.answerLeft--;
    this.answerUsed = this.answerTotal - this.answerLeft;
    this._updateRing(this.answerLeft, this.answerTotal, 'Answer time');

    if (this.answerLeft <= 0) {
      clearInterval(this.answerInterval);
      this.playEndSound();
      if (this.onAnswerEnd) this.onAnswerEnd();
    }
  },

  getTimingStats() {
    return {
      prep_seconds_used: this.prepUsed || this.prepTotal,
      answer_seconds_used: this.answerUsed,
      time_spent_seconds: this.questionStartedAt
        ? Math.round((Date.now() - this.questionStartedAt) / 1000)
        : 0,
      practice_without_timer: this.practiceWithoutTimer,
    };
  },

  destroy() {
    clearInterval(this.prepInterval);
    clearInterval(this.answerInterval);
    clearInterval(this.quizInterval);
  },
};
