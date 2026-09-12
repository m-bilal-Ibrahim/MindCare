// ============================================================
// MindCare — Therapist Console: In-session (live call)
//
// Security note: a real video session must use an encrypted transport
// (e.g. WebRTC with SRTP/DTLS) with end-to-end encryption for the media
// stream, and the backend must independently authorize that THIS
// therapist is allowed to join THIS specific session before issuing
// any call/media tokens. Live sensor + transcript data is health
// information — see src/utils/authGuard.tsx for the wider PHI notes
// that also apply here.
// ============================================================

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Video, MessageSquare, MoreHorizontal, PhoneOff, Code, Shield } from 'lucide-react';
import TherapistSidebar from '../components/therapist/TherapistSidebar';
import Sparkline from '../components/therapist/Sparkline';
import { IN_SESSION_DATA, buildPatientDetailRoute } from '../constants/therapistConsole';
import { sanitizeText, MAX_LENGTHS } from '../utils/validation';

type SidePanelTab = 'Live notes' | 'Sensors' | 'AI cues' | 'History';

const InSessionPage: React.FC = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState<SidePanelTab>('Live notes');
  const [manualNote, setManualNote] = useState('');

  const handleEndSession = () => {
    // TODO: real implementation must tear down the media connection
    // server-side too, not just navigate away client-side.
    navigate(buildPatientDetailRoute(IN_SESSION_DATA.patientId));
  };

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = sanitizeText(manualNote);
    if (!clean) return;
    // TODO: persist to real session notes endpoint
    // eslint-disable-next-line no-console
    console.info('[MindCare] Manual session note added:', clean);
    setManualNote('');
  };

  return (
    <div className="min-h-screen bg-gray-950 flex">
      <TherapistSidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Live topbar */}
        <header className="flex items-center gap-4 px-8 py-4 border-b border-white/10 bg-gray-950 text-white">
          <span className="flex items-center gap-2 text-sm font-semibold shrink-0">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" aria-hidden="true" />
            LIVE · {IN_SESSION_DATA.sessionLabel}
          </span>
          <span className="text-sm text-gray-400 shrink-0">with {IN_SESSION_DATA.patientName}</span>
          <span className="text-sm text-gray-500 shrink-0">
            {IN_SESSION_DATA.elapsedLabel} / {IN_SESSION_DATA.totalLabel}
          </span>

          <div className="ml-auto flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => navigate(buildPatientDetailRoute(IN_SESSION_DATA.patientId))}
              className="border border-white/20 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-white/10 transition-colors"
            >
              Open patient file
            </button>
            <button
              type="button"
              className="border border-white/20 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-white/10 transition-colors"
            >
              Share screen
            </button>
            <button
              type="button"
              onClick={handleEndSession}
              className="inline-flex items-center gap-2 bg-red-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-red-700 transition-colors"
            >
              <PhoneOff size={14} aria-hidden="true" /> End session
            </button>
          </div>
        </header>

        {/* Body */}
        <div className="flex-1 flex min-h-0">
          {/* Video area */}
          <div className="flex-1 relative flex flex-col items-center justify-center p-8">
            <div className="absolute top-6 left-6 flex gap-2">
              <span className="inline-flex items-center gap-1.5 bg-black/40 text-white text-xs font-semibold px-3 py-1.5 rounded-full">
                <Code size={12} aria-hidden="true" /> Aida is taking notes
              </span>
              <span className="inline-flex items-center gap-1.5 bg-black/40 text-white text-xs font-semibold px-3 py-1.5 rounded-full">
                <Shield size={12} aria-hidden="true" /> End-to-end encrypted
              </span>
            </div>

            <div
              className="w-48 h-48 rounded-full mb-6"
              style={{ background: 'radial-gradient(circle at 35% 30%, #c98a6b, #8a4a3a 70%)' }}
              aria-hidden="true"
            />
            <h1 className="text-3xl font-black text-white mb-2">{IN_SESSION_DATA.patientName}</h1>
            <p className="text-gray-400 italic">Speaking · {IN_SESSION_DATA.speakingCaption}</p>

            {/* Self view */}
            <div className="absolute bottom-28 right-8 w-48 h-32 bg-gray-800 rounded-xl border border-white/10 flex items-end p-2">
              <span className="text-xs text-white font-semibold">You</span>
              <Mic size={13} className="absolute top-2 right-2 text-white/70" aria-hidden="true" />
            </div>

            {/* AI prompt suggestion */}
            <div className="absolute bottom-28 left-8 right-64 bg-black/60 rounded-xl px-5 py-4">
              <p className="text-white italic">{IN_SESSION_DATA.aiPromptSuggestion}</p>
            </div>

            {/* Call controls */}
            <div className="absolute bottom-6 flex items-center gap-3">
              <button type="button" aria-label="Mute microphone" className="w-11 h-11 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white">
                <Mic size={16} />
              </button>
              <button type="button" aria-label="Toggle camera" className="w-11 h-11 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white">
                <Video size={16} />
              </button>
              <button type="button" aria-label="Chat" className="w-11 h-11 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white">
                <MessageSquare size={16} />
              </button>
              <button type="button" aria-label="More options" className="w-11 h-11 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white">
                <MoreHorizontal size={16} />
              </button>
              <button
                type="button"
                onClick={handleEndSession}
                aria-label="End session"
                className="w-11 h-11 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center text-white"
              >
                <PhoneOff size={16} />
              </button>
            </div>
          </div>

          {/* Side panel */}
          <aside className="w-96 shrink-0 bg-[#F5F0E8] flex flex-col border-l border-black/10">
            <div className="flex border-b border-gray-200 px-4">
              {(['Live notes', 'Sensors', 'AI cues', 'History'] as SidePanelTab[]).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setTab(t)}
                  className={`px-3 py-4 text-sm font-semibold border-b-2 transition-colors ${
                    tab === t ? 'text-gray-900 border-gray-900' : 'text-gray-400 border-transparent hover:text-gray-600'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {/* Live sensors — shown on every tab except History, matching design */}
              {tab !== 'History' && (
                <div className="grid grid-cols-3 gap-3 mb-5">
                  {IN_SESSION_DATA.liveSensors.map((s) => (
                    <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-3">
                      <p className="text-[10px] font-semibold tracking-widest text-gray-500 uppercase mb-1">
                        {s.label}
                      </p>
                      <p className="text-xl font-black text-gray-900 mb-1">{s.value}</p>
                      <Sparkline data={s.trend} color={s.color} height={20} />
                    </div>
                  ))}
                </div>
              )}

              {tab === 'Live notes' && (
                <>
                  <div className="bg-[#EFE9DF] rounded-xl p-4 mb-4">
                    <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">
                      Session notes · autosaved 12s ago
                    </p>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {IN_SESSION_DATA.liveNotes.find((n) => n.type === 'auto')?.content}
                    </p>
                  </div>

                  {IN_SESSION_DATA.liveNotes
                    .filter((n) => n.type === 'marked')
                    .map((n) => (
                      <div key={n.id} className="bg-white border border-gray-200 rounded-xl p-4 mb-4">
                        <p className="text-sm text-gray-800">
                          <span className="font-bold">Marked</span> · {n.time} — {n.content}
                        </p>
                      </div>
                    ))}

                  {IN_SESSION_DATA.liveNotes
                    .filter((n) => n.type === 'auto')
                    .slice(1)
                    .map((n) => (
                      <p key={n.id} className="text-sm text-gray-700 leading-relaxed mb-4">
                        {n.content}
                      </p>
                    ))}

                  <form onSubmit={handleAddNote}>
                    <input
                      type="text"
                      value={manualNote}
                      onChange={(e) => setManualNote(e.target.value.slice(0, MAX_LENGTHS.longText))}
                      maxLength={MAX_LENGTHS.longText}
                      placeholder="Type here to add…"
                      className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-gray-900"
                    />
                  </form>
                </>
              )}

              {tab === 'Sensors' && (
                <p className="text-sm text-gray-500 leading-relaxed">
                  Full sensor history for this session (heart rate, breathing, EDA) will chart here once the
                  session ends — live values are shown above.
                </p>
              )}

              {tab === 'AI cues' && (
                <div className="bg-white border border-gray-200 rounded-xl p-4">
                  <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">
                    Aida · live cues
                  </p>
                  <p className="text-sm text-gray-800 leading-relaxed mb-4">{IN_SESSION_DATA.liveCue}</p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800"
                    >
                      Try grounding
                    </button>
                    <button
                      type="button"
                      className="bg-white border border-gray-200 text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400"
                    >
                      Mark moment
                    </button>
                  </div>
                </div>
              )}

              {tab === 'History' && (
                <p className="text-sm text-gray-500 leading-relaxed">
                  Past session notes for {IN_SESSION_DATA.patientName} are available on their{' '}
                  <button
                    type="button"
                    onClick={() => navigate(buildPatientDetailRoute(IN_SESSION_DATA.patientId))}
                    className="underline underline-offset-2 font-semibold text-gray-800"
                  >
                    patient detail page
                  </button>
                  .
                </p>
              )}
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default InSessionPage;