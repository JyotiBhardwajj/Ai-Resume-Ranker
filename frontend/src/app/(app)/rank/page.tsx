'use client';

import * as React from 'react';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MagnifyingGlass,
  Sparkle,
  WarningCircle,
  User,
  Brain,
  Warning,
  ShieldCheck,
  Scales,
  X,
  Trophy,
  CaretDown,
  CaretUp,
  Lightning,
  Star,
  CircleNotch,
  CheckCircle,
  EnvelopeSimple,
  Copy,
  Plus,
  Minus,
  CloudArrowUp
} from '@phosphor-icons/react';
import { FileUpload } from '@/components/ui/file-upload';

interface Candidate {
  id: string;
  name: string;
  currentRole: string;
  experience: string;
  matchScore: number;
  matchReason: string;
  skills: string[];
  status: 'highly-recommended' | 'recommended' | 'hidden-gem' | 'underqualified';
}

const mockCandidates: Candidate[] = [
  {
    id: 'CAND_0000001',
    name: 'Aishwarya Sen',
    currentRole: 'Senior Software Engineer',
    experience: '6 years',
    matchScore: 97,
    matchReason: 'Perfect technical stack alignment. Led transition to microservices and has deep Golang/React domain expertise.',
    skills: ['Golang', 'React', 'Kubernetes', 'REST APIs'],
    status: 'highly-recommended',
  },
  {
    id: 'CAND_0000002',
    name: 'Rahul Sharma',
    currentRole: 'Backend Engineer',
    experience: '4 years',
    matchScore: 92,
    matchReason: 'Strong systems background and database tuning experience. Ex-Amazon with strong distributed systems design foundations.',
    skills: ['Golang', 'PostgreSQL', 'Redis', 'Docker'],
    status: 'highly-recommended',
  },
  {
    id: 'CAND_0000003',
    name: 'Priyanka Patel',
    currentRole: 'Full Stack Consultant',
    experience: '3 years',
    matchScore: 89,
    matchReason: 'Classified as a Hidden Gem. Though her title is Consultant, her actual projects exhibit senior-level architectural design in cloud systems.',
    skills: ['React', 'Node.js', 'AWS', 'TypeScript'],
    status: 'hidden-gem',
  },
  {
    id: 'CAND_0000004',
    name: 'Vikram Singh',
    currentRole: 'Software Developer',
    experience: '5 years',
    matchScore: 81,
    matchReason: 'Solid developer, but lacks Golang production experience. Strong in Python and willing to pivot.',
    skills: ['Python', 'Django', 'PostgreSQL', 'AWS'],
    status: 'recommended',
  },
  {
    id: 'CAND_0000005',
    name: 'Neha Gupta',
    currentRole: 'QA Automation Engineer',
    experience: '3 years',
    matchScore: 48,
    matchReason: 'Primarily automation and testing background. Insufficient software design and system engineering alignment.',
    skills: ['Python', 'Selenium', 'CI/CD', 'Jest'],
    status: 'underqualified',
  },
];

const STATUS_CONFIG = {
  'highly-recommended': {
    label: 'Top Match',
    className: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
    scoreBar: 'bg-emerald-500',
    avatarClass: 'bg-emerald-500/12 text-emerald-700 border-emerald-500/25',
  },
  'recommended': {
    label: 'Recommended',
    className: 'bg-foreground/8 text-foreground border-foreground/15',
    scoreBar: 'bg-foreground/60',
    avatarClass: 'bg-muted text-muted-foreground border-border/50',
  },
  'hidden-gem': {
    label: '✦ Hidden Gem',
    className: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
    scoreBar: 'bg-amber-500',
    avatarClass: 'bg-amber-500/12 text-amber-700 border-amber-500/25',
  },
  'underqualified': {
    label: 'Low Match',
    className: 'bg-muted text-muted-foreground border-border/50',
    scoreBar: 'bg-muted-foreground/40',
    avatarClass: 'bg-muted text-muted-foreground/60 border-border/30',
  },
};

export default function RankPage() {
  const [search, setSearch] = React.useState('');
  const [filter, setFilter] = React.useState<'all' | 'top' | 'recommended'>('all');
  const [candidates, setCandidates] = React.useState<Candidate[]>([]);
  const [isRanking, setIsRanking] = React.useState(false);
  const [jdText, setJdText] = React.useState<string>('');

  const [expandedId, setExpandedId] = React.useState<string | null>(null);
  const [copilotData, setCopilotData] = React.useState<any>(null);
  const [isGeneratingCopilot, setIsGeneratingCopilot] = React.useState(false);
  const [riskData, setRiskData] = React.useState<any>(null);
  const [isAnalyzingRisk, setIsAnalyzingRisk] = React.useState(false);

  const [selectedForCompare, setSelectedForCompare] = React.useState<string[]>([]);
  const [compareData, setCompareData] = React.useState<any>(null);
  const [isComparing, setIsComparing] = React.useState(false);
  const [showCompareModal, setShowCompareModal] = React.useState(false);
  const [showEmailAccordion, setShowEmailAccordion] = React.useState(false);

  const [isCustomMode, setIsCustomMode] = React.useState(false);
  const [showUploadModal, setShowUploadModal] = React.useState(false);

  const getCache = (type: 'copilot' | 'risk' | 'compare', key: string) => {
    try {
      const data = localStorage.getItem(`talentIntelCache_${type}`);
      if (data) return JSON.parse(data)[key];
    } catch { }
    return null;
  };

  const setCache = (type: 'copilot' | 'risk' | 'compare', key: string, val: any) => {
    try {
      const current = localStorage.getItem(`talentIntelCache_${type}`);
      const data = current ? JSON.parse(current) : {};
      data[key] = val;
      localStorage.setItem(`talentIntelCache_${type}`, JSON.stringify(data));
    } catch { }
  };

  const expandedCandidate = candidates.find(c => c.id === expandedId) || null;

  React.useEffect(() => {
    const savedJd = localStorage.getItem('talentIntelJD');
    if (savedJd) setJdText(savedJd);

    const autoRun = localStorage.getItem('talentIntelAutoRunRank');
    const cacheKey = `talentIntelRankedCandidates_${isCustomMode ? 'custom' : 'static'}`;
    const savedCandidates = localStorage.getItem(cacheKey) || localStorage.getItem('talentIntelRankedCandidates');

    if (savedCandidates && autoRun !== 'true') {
      try {
        setCandidates(JSON.parse(savedCandidates));
      } catch (e) {
        console.error('Failed to parse saved candidates', e);
      }
    }

    if (autoRun === 'true') {
      localStorage.removeItem('talentIntelAutoRunRank');
      // Execute rank immediately with the saved JD
      setTimeout(() => {
        executeRank(savedJd || jdText, isCustomMode, true);
      }, 0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleExpand = (id: string) => {
    if (expandedId === id) { setExpandedId(null); setCopilotData(null); setRiskData(null); setShowEmailAccordion(false); }
    else { setExpandedId(id); setCopilotData(null); setRiskData(null); setShowEmailAccordion(false); }
  };

  const handleGenerateCopilot = async () => {
    if (!expandedCandidate) return;
    const cached = getCache('copilot', expandedCandidate.id);
    if (cached) {
      setCopilotData(cached);
      return;
    }

    setIsGeneratingCopilot(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/candidates/copilot`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: expandedCandidate.id, jd_text: jdText || 'Senior Golang / React Developer' })
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setCopilotData(data);
      setCache('copilot', expandedCandidate.id, data);
    } catch { toast.error('Failed to generate interview guide'); }
    finally { setIsGeneratingCopilot(false); }
  };

  const handleAnalyzeRisk = async () => {
    if (!expandedCandidate) return;
    const cached = getCache('risk', expandedCandidate.id);
    if (cached) {
      setRiskData(cached);
      return;
    }

    setIsAnalyzingRisk(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/candidates/risk`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_id: expandedCandidate.id, jd_text: jdText || 'Senior Golang / React Developer' })
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setRiskData(data);
      setCache('risk', expandedCandidate.id, data);
    } catch { toast.error('Failed to run Risk Analysis'); }
    finally { setIsAnalyzingRisk(false); }
  };

  const toggleCompare = (id: string) => {
    setSelectedForCompare(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : prev.length < 3 ? [...prev, id] : prev
    );
  };

  const handleCompare = async () => {
    if (selectedForCompare.length < 2) return;
    const compareKey = [...selectedForCompare].sort().join(',');
    const cached = getCache('compare', compareKey);
    if (cached) {
      setCompareData(cached);
      setShowCompareModal(true);
      return;
    }

    setIsComparing(true); setShowCompareModal(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/candidates/compare`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ candidate_ids: selectedForCompare, jd_text: jdText || 'Senior Golang / React Developer' })
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setCompareData(data);
      setCache('compare', compareKey, data);
    } catch { toast.error('Compare Engine failed.'); setShowCompareModal(false); }
    finally { setIsComparing(false); }
  };

  const executeRank = async (jdToUse: string, isCustom: boolean, force: boolean) => {
    setIsRanking(true);

    const cacheKey = `talentIntelRankedCandidates_${isCustom ? 'custom' : 'static'}`;

    if (!force) {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        try {
          setCandidates(JSON.parse(cached));
          setIsRanking(false);
          return;
        } catch {}
      }
    }

    // Invalidate caches for new rank run
    localStorage.removeItem('talentIntelCache_copilot');
    localStorage.removeItem('talentIntelCache_risk');
    localStorage.removeItem('talentIntelCache_compare');

    try {
      const { createClient } = await import('@/utils/supabase/client');
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const userId = session?.user?.id;

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const payloadText = jdToUse || `Senior Software Engineer with 5+ years in Golang and React.`;
      const res = await fetch(`${apiUrl}/api/jd/match`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: payloadText, is_custom: isCustom, user_id: userId })
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      const map = (c: any, top: boolean): Candidate => {
        const p = c.profile || c.profile_data || {};
        let status: Candidate['status'] = top ? 'highly-recommended' : 'recommended';

        // Hidden Gem logic: High semantic fit but low domain fit
        if (c.semantic_score >= 70 && c.domain_score <= 45) {
          status = 'hidden-gem';
        } else if (c.final_score < 50) {
          status = 'underqualified';
        }

        return {
          id: c.candidate_id,
          name: p.anonymized_name || p.name || 'Anonymous',
          currentRole: p.current_title || p.current_role || 'Professional',
          experience: p.years_of_experience ? `${p.years_of_experience} years` : `${Math.round((p.experience_months || 0) / 12)} years`,
          matchScore: Math.round(c.final_score) || 0,
          matchReason: `Semantic: ${Math.round(c.semantic_score)}% · Domain: ${Math.round(c.domain_score)}%\n\n${p.summary || ''}`,
          skills: c.skills || p.skills || [],
          status: status,
        };
      };
      const newCandidates = [
        ...(data.top_candidates || []).map((c: any) => map(c, true)),
        ...(data.considered_candidates || []).map((c: any) => map(c, false)),
      ];
      setCandidates(newCandidates);
      localStorage.setItem(cacheKey, JSON.stringify(newCandidates));
      localStorage.setItem('talentIntelRankedCandidates', JSON.stringify(newCandidates));
    } catch { toast.error('Failed to connect to ranking engine.'); }
    finally { setIsRanking(false); }
  };

  const handleRank = (e?: React.MouseEvent | string) => {
    let jd = typeof e === 'string' ? e : jdText;
    executeRank(jd, isCustomMode, true);
  };

  const filtered = candidates.filter(c => {
    const q = search.toLowerCase();
    const hit = c.name.toLowerCase().includes(q) || c.skills.some(s => s.toLowerCase().includes(q));
    if (filter === 'top') return hit && c.status === 'highly-recommended';
    if (filter === 'recommended') return hit && c.status === 'recommended';
    return hit;
  });

  const formattedReasoning = React.useMemo(() => {
    if (!compareData?.reasoning) return '';
    let text = compareData.reasoning;
    selectedForCompare.forEach(id => {
      const c = candidates.find(cand => cand.id === id);
      if (c) {
        text = text.replaceAll(id, c.name);
      }
    });
    return text;
  }, [compareData, selectedForCompare, candidates]);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-1">Step 2 of 2</p>
          <h1 className="text-2xl font-bold tracking-tight">Candidate Ranking</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {!jdText ? 'No JD analyzed yet — using default criteria.' : 'Ranked against your analyzed job description.'}
          </p>
        </div>
        <button
          onClick={handleRank}
          disabled={isRanking}
          className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground shadow-md rounded-xl text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 active:scale-[0.98] transition-all cursor-pointer shrink-0 self-start"
        >
          {isRanking
            ? <><CircleNotch size={15} className="animate-spin" />Ranking...</>
            : <><Sparkle size={15} weight="duotone" />Run Ranking Engine</>}
        </button>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
        <div className="relative flex-1 max-w-sm">
          <MagnifyingGlass size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            placeholder="Search by name or skill..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-background border border-border/60 rounded-xl pl-10 pr-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-foreground/30 focus:ring-1 focus:ring-foreground/10 transition-all"
          />
        </div>
        <div className="flex items-center bg-muted/50 border border-border/50 rounded-xl p-1 relative">
          {(['all', 'top', 'recommended'] as const).map(f => {
            const isActive = filter === f;
            return (
              <button key={f} onClick={() => setFilter(f)}
                className={`relative px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer z-10 ${isActive ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`}>
                {isActive && (
                  <motion.div
                    layoutId="filterTab"
                    className="absolute inset-0 bg-background shadow-sm border border-border/60 rounded-lg -z-10"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                {f === 'all' ? 'All' : f === 'top' ? 'Top Match' : 'Recommended'}
              </button>
            );
          })}
        </div>

        <div className="flex items-center bg-muted/50 border border-border/50 rounded-xl p-1 relative ml-2">
          <button
            onClick={() => {
              setIsCustomMode(false);
              setTimeout(() => executeRank(jdText, false, false), 0);
            }}
            className={`relative px-3 py-1 rounded-lg text-xs font-semibold transition-colors z-10 ${!isCustomMode ? 'bg-background shadow-sm text-foreground border border-border/60' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Static Pool
          </button>
          <button
            onClick={() => {
              setIsCustomMode(true);
              setTimeout(() => executeRank(jdText, true, false), 0);
            }}
            className={`relative px-3 py-1 rounded-lg text-xs font-semibold transition-colors z-10 ${isCustomMode ? 'bg-background shadow-sm text-foreground border border-border/60' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Custom Resumes
          </button>
        </div>

        <button 
          onClick={() => setShowUploadModal(true)}
          className="flex items-center gap-2 px-3.5 py-1.5 border border-primary/20 bg-primary/5 hover:bg-primary/10 text-primary rounded-xl text-xs font-bold transition-colors shadow-sm ml-auto"
        >
          <CloudArrowUp size={16} weight="duotone" />
          Upload Resumes
        </button>

        <span className="text-xs text-muted-foreground font-medium self-center shrink-0 ml-2">
          {filtered.length} candidate{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <div className="bg-card w-full max-w-2xl border border-border shadow-lg rounded-2xl p-6 relative">
            <button 
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
              onClick={() => setShowUploadModal(false)}
            >
              <X size={20} />
            </button>
            <h2 className="text-xl font-bold mb-2">Upload Custom Resumes</h2>
            <p className="text-sm text-muted-foreground mb-6">
              Drop PDF resumes here. They will be parsed by Gemini, embedded, and saved securely to your private candidate pool.
            </p>
            <FileUpload 
              onUploadComplete={() => {
                setShowUploadModal(false);
                setIsCustomMode(true);
                executeRank(jdText, true, true);
              }}
            />
          </div>
        </div>
      )}

      {/* List */}
      <div className="space-y-2">
        {isRanking && Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="bg-card border border-border/50 rounded-2xl p-5 animate-pulse">
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-muted shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-muted rounded-lg w-40" />
                <div className="h-3 bg-muted rounded-lg w-56" />
              </div>
              <div className="h-8 bg-muted rounded-lg w-20" />
            </div>
          </div>
        ))}

        {!isRanking && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 bg-card border border-border/50 rounded-2xl gap-3">
            {isCustomMode ? (
              <>
                <CloudArrowUp size={40} weight="duotone" className="text-primary/40" />
                <p className="text-sm font-semibold text-foreground">No custom resumes found</p>
                <p className="text-xs text-muted-foreground max-w-sm text-center mb-2">
                  Upload resumes to test and rank your own candidates against the current Job Description.
                </p>
                <button 
                  onClick={() => setShowUploadModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-xl text-xs font-bold transition-colors shadow-sm"
                >
                  <CloudArrowUp size={16} weight="bold" />
                  Upload Resumes Now
                </button>
              </>
            ) : (
              <>
                <WarningCircle size={40} weight="duotone" className="text-muted-foreground/40" />
                <p className="text-sm font-semibold text-muted-foreground">No candidates found</p>
              </>
            )}
          </div>
        )}

        {!isRanking && filtered.map((cand, index) => {
          const cfg = STATUS_CONFIG[cand.status];
          const isExpanded = expandedId === cand.id;
          const isSelected = selectedForCompare.includes(cand.id);

          return (
            <div key={cand.id} className={`bg-card border rounded-2xl overflow-hidden transition-all duration-200 ${isExpanded ? 'border-foreground/20 shadow-md' : 'border-border/50 hover:border-border'}`}>
              {/* Row */}
              <div className="flex items-center gap-4 px-5 py-4">
                <span className="text-xs font-bold text-muted-foreground/40 w-5 text-center shrink-0">{index + 1}</span>

                {/* Monogram avatar */}
                <div className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold shrink-0 border ${cfg.avatarClass}`}>
                  {cand.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm text-foreground">{cand.name}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${cfg.className}`}>{cfg.label}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 truncate">{cand.currentRole} · {cand.experience}</p>
                </div>

                {/* Skills desktop */}
                <div className="hidden lg:flex items-center gap-1.5 shrink-0 max-w-[280px] overflow-hidden whitespace-nowrap">
                  {cand.skills.slice(0, 3).map(s => (
                    <span key={s} className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-muted border border-border/50 text-muted-foreground truncate max-w-[100px]">{s}</span>
                  ))}
                  {cand.skills.length > 3 && <span className="text-[10px] font-bold px-1.5 py-0.5 text-muted-foreground/60 shrink-0">+{cand.skills.length - 3}</span>}
                </div>

                {/* Score */}
                <div className="hidden sm:flex flex-col items-end gap-1 shrink-0">
                  <span className="text-lg font-bold text-foreground leading-none">{cand.matchScore}%</span>
                  <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${cfg.scoreBar}`} style={{ width: `${cand.matchScore}%` }} />
                  </div>
                </div>

                {/* Compare */}
                <div className="flex flex-col items-end justify-center shrink-0 w-[100px] relative group">
                  {!isSelected && selectedForCompare.length >= 3 && (
                    <span className="absolute top-full mt-2 right-0 text-[10px] font-medium text-gray-500 bg-transparent shadow-lg border border-border/50 px-2.5 py-1 rounded-md whitespace-nowrap hidden sm:block opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                      can only compare 3 candidates
                    </span>
                  )}
                  <label className={`flex items-center gap-1.5 ${!isSelected && selectedForCompare.length >= 3 ? 'cursor-not-allowed opacity-60' : 'cursor-pointer hover:opacity-80'}`}>
                    <input type="checkbox" checked={isSelected} onChange={() => toggleCompare(cand.id)}
                      disabled={!isSelected && selectedForCompare.length >= 3}
                      className={`h-4 w-4 rounded border-border/60 ${!isSelected && selectedForCompare.length >= 3 ? 'cursor-not-allowed' : 'cursor-pointer'}`} />
                    <span className="text-[10px] text-foreground font-medium hidden sm:block">Compare</span>
                  </label>
                </div>

                {/* Expand */}
                <button onClick={() => toggleExpand(cand.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer shrink-0 ${isExpanded ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted hover:bg-muted/80 text-foreground border border-border/50'}`}>
                  {isExpanded ? <CaretUp size={12} weight="bold" /> : <CaretDown size={12} weight="bold" />}
                  {isExpanded ? 'Close' : 'Details'}
                </button>
              </div>

              {/* Expandable panel */}
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                    className="overflow-hidden border-t border-border/50 bg-muted/20"
                  >
                    <div className="p-5 space-y-6">
                      {/* Match Reason */}
                      <div className="flex gap-3">
                        <div>
                          <p className="text-xs font-bold text-foreground mb-1">AI Match Reasoning</p>
                          <p className="text-sm text-muted-foreground leading-relaxed">{cand.matchReason}</p>
                        </div>
                      </div>

                      {/* Skills */}
                      <div>
                        <p className="text-xs font-bold text-foreground mb-2">Extracted Skills</p>
                        <div className="flex flex-wrap gap-1.5">
                          {cand.skills.map(s => (
                            <span key={s} className="text-xs font-medium px-2.5 py-1 rounded-lg border border-border/60 bg-background text-foreground">{s}</span>
                          ))}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-wrap gap-2 pt-1">
                        <button onClick={handleGenerateCopilot} disabled={isGeneratingCopilot}
                          className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground shadow-sm rounded-xl text-xs font-semibold disabled:opacity-50 hover:bg-secondary/90 active:scale-[0.98] transition-all cursor-pointer">
                          {isGeneratingCopilot ? <><CircleNotch size={13} className="animate-spin" />Generating...</> : <><Brain size={13} weight="duotone" />Interview Copilot</>}
                        </button>
                        <button onClick={handleAnalyzeRisk} disabled={isAnalyzingRisk}
                          className="flex items-center gap-2 px-4 py-2 bg-background text-foreground border border-border/60 rounded-xl text-xs font-semibold disabled:opacity-50 hover:bg-muted active:scale-[0.98] transition-all cursor-pointer">
                          {isAnalyzingRisk ? <><CircleNotch size={13} className="animate-spin" />Analyzing...</> : <><Warning size={13} weight="duotone" className="text-destructive" />Risk Profile</>}
                        </button>
                      </div>

                      {/* Risk */}
                      <AnimatePresence>
                        {riskData && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden border-t border-border/50 pt-5 space-y-4"
                          >
                            <div className="flex items-center justify-between">
                              <p className="text-xs font-bold text-foreground uppercase tracking-wider">Risk Profile</p>
                              <span className={`text-xs font-bold px-2.5 py-1 rounded-lg border ${riskData.risk_level === 'High' ? 'bg-red-500/10 text-red-600 border-red-500/20' : riskData.risk_level === 'Medium' ? 'bg-amber-500/10 text-amber-600 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'}`}>
                                {riskData.risk_level} Risk · {riskData.risk_score_0_to_100}/100
                              </span>
                            </div>
                            <div className="grid sm:grid-cols-2 gap-4">
                              <div>
                                <p className="text-[11px] font-bold uppercase tracking-wider text-rose-500 mb-2 flex items-center gap-1"><Warning size={11} weight="fill" />Risk Factors</p>
                                <ul className="space-y-1">{riskData.risk_factors?.map((rf: string, i: number) => <li key={i} className="text-xs text-muted-foreground flex gap-2"><span className="text-rose-400 shrink-0">·</span>{rf}</li>)}</ul>
                              </div>
                              <div>
                                <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-600 mb-2 flex items-center gap-1"><ShieldCheck size={11} weight="fill" />Mitigating Factors</p>
                                <ul className="space-y-1">{riskData.mitigating_factors?.map((mf: string, i: number) => <li key={i} className="text-xs text-muted-foreground flex gap-2"><span className="text-emerald-500 shrink-0">·</span>{mf}</li>)}</ul>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Copilot */}
                      <AnimatePresence>
                        {copilotData && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden border-t border-border/50 pt-5 space-y-4"
                          >
                            <p className="text-xs font-bold text-foreground uppercase tracking-wider">Interview Copilot</p>
                            <div className="space-y-4">
                              <div className="bg-background border border-border/50 rounded-xl p-4">
                                <h4 className="text-xs font-bold text-foreground flex items-center gap-2 mb-3"><Brain size={14} className="text-primary" /> Technical Assessment</h4>
                                <ul className="space-y-2">
                                  {copilotData.technical_questions?.map((q: string, i: number) => (
                                    <li key={i} className="text-xs text-muted-foreground flex gap-2"><span className="text-primary shrink-0 mt-0.5">•</span> <span className="leading-relaxed">{q}</span></li>
                                  ))}
                                </ul>
                              </div>
                              <div className="bg-background border border-border/50 rounded-xl p-4">
                                <h4 className="text-xs font-bold text-foreground flex items-center gap-2 mb-3"><Lightning size={14} className="text-amber-500" /> Areas to Probe</h4>
                                <ul className="space-y-2">
                                  {copilotData.areas_to_probe?.map((q: string, i: number) => (
                                    <li key={i} className="text-xs text-muted-foreground flex gap-2"><span className="text-amber-500 shrink-0 mt-0.5">•</span> <span className="leading-relaxed">{q}</span></li>
                                  ))}
                                </ul>
                              </div>
                              <div className="bg-background border border-border/50 rounded-xl p-4">
                                <h4 className="text-xs font-bold text-foreground flex items-center gap-2 mb-3"><User size={14} className="text-emerald-500" /> Behavioral & Culture Fit</h4>
                                <ul className="space-y-2">
                                  {copilotData.behavioral_questions?.map((q: string, i: number) => (
                                    <li key={i} className="text-xs text-muted-foreground flex gap-2"><span className="text-emerald-500 shrink-0 mt-0.5">•</span> <span className="leading-relaxed">{q}</span></li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                            {copilotData.personalized_outreach_email && (
                              <div className="bg-primary/5 border border-primary/20 rounded-xl overflow-hidden transition-all mt-4">
                                <button
                                  onClick={() => setShowEmailAccordion(!showEmailAccordion)}
                                  className="w-full flex items-center justify-between p-4 cursor-pointer hover:bg-primary/10 transition-colors"
                                >
                                  <div className="flex items-center gap-2">
                                    <EnvelopeSimple size={16} weight="duotone" className="text-primary" />
                                    <h4 className="text-xs font-bold text-primary">Outreach Email Draft</h4>
                                  </div>
                                  {showEmailAccordion ? <Minus size={14} weight="bold" className="text-primary" /> : <Plus size={14} weight="bold" className="text-primary" />}
                                </button>
                                {showEmailAccordion && (
                                  <div className="p-4 pt-0 border-t border-primary/10 animate-in slide-in-from-top-2 fade-in duration-200 ">
                                    <div className="bg-background rounded-lg p-4 border border-border/50 text-xs text-foreground mt-2 whitespace-pre-wrap leading-relaxed relative group">
                                      {copilotData.personalized_outreach_email}
                                      <button
                                        onClick={() => {
                                          navigator.clipboard.writeText(copilotData.personalized_outreach_email);
                                          toast.success("Email copied to clipboard!");
                                        }}
                                        className="absolute top-2 right-2 p-1.5 bg-muted hover:bg-muted-foreground/20 rounded-md opacity-100 transition-opacity cursor-pointer text-muted-foreground"
                                        title="Copy to clipboard"
                                      >
                                        <Copy size={14} weight="duotone" />
                                      </button>
                                    </div>
                                    <div className="mt-3 flex justify-end">
                                      <button onClick={() => setShowEmailAccordion(false)} className="text-[11px] font-bold text-primary hover:underline cursor-pointer">
                                        Close Draft
                                      </button>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      {/* Compare Bar */}
      {selectedForCompare.length >= 2 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 animate-in slide-in-from-bottom-4 fade-in duration-250">
          <div className="bg-primary text-primary-foreground px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-4 border border-primary/20">
            <Scales size={16} weight="duotone" className="shrink-0" />
            <span className="text-sm font-semibold">{selectedForCompare.length} selected</span>
            <button onClick={handleCompare} className="bg-background text-foreground hover:bg-muted rounded-xl px-4 py-1.5 text-xs font-bold border border-border/50 cursor-pointer transition-colors shadow-sm">
              Compare →
            </button>
            <button onClick={() => setSelectedForCompare([])} className="cursor-pointer hover:opacity-70 transition-opacity">
              <X size={15} weight="bold" />
            </button>
          </div>
        </div>
      )}

      {/* Compare Modal */}
      {showCompareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8">
          <div className="absolute inset-0 bg-background/70 backdrop-blur-sm" onClick={() => setShowCompareModal(false)} />
          <div className="relative bg-card w-full max-w-5xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl border border-border flex flex-col animate-in zoom-in-95 duration-200">
            <div className="sticky top-0 bg-card/95 backdrop-blur-md border-b border-border/50 px-6 py-4 flex items-center justify-between z-10">
              <div>
                <h2 className="text-base font-bold flex items-center gap-2"><Scales size={16} weight="duotone" /> Comparison Engine</h2>
                <p className="text-xs text-muted-foreground mt-0.5">AI-driven side-by-side analysis</p>
              </div>
              <button onClick={() => setShowCompareModal(false)} className="p-2 hover:bg-muted rounded-xl cursor-pointer">
                <X size={15} weight="bold" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              {isComparing ? (
                <div className="flex flex-col items-center justify-center py-24 gap-4">
                  <Scales size={40} weight="duotone" className="text-foreground/30 animate-pulse" />
                  <p className="text-sm font-semibold text-muted-foreground">Running comparative analysis...</p>
                </div>
              ) : compareData ? (
                <div className="space-y-6">
                  {formattedReasoning && (
                    <div className="flex items-start gap-4 bg-emerald-500/8 border border-emerald-500/20 rounded-2xl p-5">
                      <Trophy size={18} weight="duotone" className="text-emerald-600 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-bold text-emerald-700 dark:text-emerald-400 mb-1">Recommended Hire</p>
                        <p className="text-sm text-foreground leading-relaxed">{formattedReasoning}</p>
                      </div>
                    </div>
                  )}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {compareData.comparisons?.map((comp: any) => {
                      const info = candidates.find(c => c.id === comp.candidate_id);
                      const isWinner = compareData.recommended_candidate_id === comp.candidate_id;
                      return (
                        <div key={comp.candidate_id} className={`bg-background rounded-2xl border p-5 space-y-4 ${isWinner ? 'border-emerald-500/40' : 'border-border/50'}`}>
                          <div className="flex items-center gap-3 pb-4 border-b border-border/50">
                            <div className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold shrink-0 border ${isWinner ? 'bg-emerald-500/15 text-emerald-700 border-emerald-500/25' : 'bg-muted text-muted-foreground border-border'}`}>
                              {info?.name.split(' ').map(n => n[0]).join('').slice(0, 2) || '?'}
                            </div>
                            <div className="min-w-0">
                              <p className="font-bold text-sm truncate">{info?.name || comp.candidate_id}</p>
                              <p className="text-[11px] text-muted-foreground truncate">{info?.currentRole}</p>
                            </div>
                            {isWinner && <Star size={14} weight="fill" className="text-emerald-500 shrink-0 ml-auto" />}
                          </div>
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 mb-2 flex items-center gap-1"><ShieldCheck size={11} weight="fill" />Strengths</p>
                            <ul className="space-y-1.5">{comp.strengths?.map((s: string, i: number) => <li key={i} className="text-xs text-muted-foreground flex gap-1.5"><span className="text-emerald-500 shrink-0">+</span>{s}</li>)}</ul>
                          </div>
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-rose-500 mb-2 flex items-center gap-1"><Warning size={11} weight="fill" />Weaknesses</p>
                            <ul className="space-y-1.5">{comp.weaknesses?.map((w: string, i: number) => <li key={i} className="text-xs text-muted-foreground flex gap-1.5"><span className="text-rose-400 shrink-0">−</span>{w}</li>)}</ul>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : <div className="text-center py-12 text-muted-foreground text-sm">No data available</div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
