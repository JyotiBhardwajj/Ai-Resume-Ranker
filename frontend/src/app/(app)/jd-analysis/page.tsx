'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import {
  Brain,
  FileText,
  CheckCircle,
  Warning,
  ArrowRight,
  Play,
  CircleNotch,
  Sparkle,
} from '@phosphor-icons/react';

export default function JdAnalysisPage() {
  const router = useRouter();
  const [jdText, setJdText] = React.useState(
    `We are looking for a Senior Software Engineer with 5+ years of experience in Golang and React. The candidate must be comfortable building RESTful APIs, working with Docker/Kubernetes, and managing PostgreSQL databases. Experience with microservice architectures and AWS is a major plus.`
  );
  const [jobTitle, setJobTitle] = React.useState('Senior Golang / React Developer');
  const [analyzed, setAnalyzed] = React.useState(false);
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [extractedData, setExtractedData] = React.useState<any>(null);

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const fullText = `Job Title: ${jobTitle}\n\n${jdText}`;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/jd/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: fullText })
      });
      if (!res.ok) throw new Error('Failed to parse JD');
      const data = await res.json();
      setExtractedData(data);
      localStorage.setItem('talentIntelJD', fullText);
      localStorage.setItem('talentIntelJDText', jdText);
      localStorage.setItem('talentIntelJobTitle', jobTitle);
      localStorage.setItem('talentIntelExtractedData', JSON.stringify(data));
      setAnalyzed(true);
    } catch (e: any) {
      toast.error('Could not reach the AI engine. Check that the backend is running.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const requiredSkills = extractedData?.structured_jd?.required_skills || [];
  const optionalSkills = extractedData?.structured_jd?.nice_to_have_skills || [];
  const minExp = extractedData?.structured_jd?.min_experience_years || 0;
  const role = extractedData?.structured_jd?.role || jobTitle;

  React.useEffect(() => {
    const savedJdText = localStorage.getItem('talentIntelJDText');
    const savedJobTitle = localStorage.getItem('talentIntelJobTitle');
    const savedExtractedData = localStorage.getItem('talentIntelExtractedData');

    if (savedJdText) setJdText(savedJdText);
    if (savedJobTitle) setJobTitle(savedJobTitle);
    if (savedExtractedData) {
      try {
        setExtractedData(JSON.parse(savedExtractedData));
        setAnalyzed(true);
      } catch (e) {
        console.error('Failed to parse saved extracted data', e);
      }
    }
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-10">
      {/* Page header */}
      <div>
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-1">Step 1 of 2</p>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Analyze Job Description</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Paste your JD and let the AI extract skills, seniority signals, and ranking criteria.
        </p>
      </div>

      {/* Main Form Card */}
      <div className="bg-card border border-border/60 rounded-2xl overflow-hidden shadow-sm">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/50 bg-muted/30">
          <div className="flex items-center gap-2.5">
            <FileText size={15} weight="duotone" className="text-muted-foreground" />
            <span className="text-sm font-semibold text-foreground">Job Description Input</span>
          </div>
          <button
            onClick={() => { setJdText(''); setJobTitle(''); }}
            className="text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
          >
            Clear
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-muted-foreground ">
              Job Title
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="w-full bg-background border border-border/60 rounded-xl px-4 py-3 text-sm font-medium text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-foreground/30 focus:ring-1 focus:ring-foreground/10 transition-all"
              placeholder="e.g. Senior Backend Engineer"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-muted-foreground ">
              Job Description Content
            </label>
            <textarea
              rows={9}
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              className="w-full bg-background border border-border/60 rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-foreground/30 focus:ring-1 focus:ring-foreground/10 transition-all font-sans leading-relaxed resize-y"
              placeholder="Paste the full job description here..."
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-4">
              <p className="text-xs text-muted-foreground">
                {jdText.length} characters · {jdText.trim().split(/\s+/).length} words
              </p>
            </div>
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !jdText.trim()}
              className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground shadow-md rounded-xl text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 active:scale-[0.98] transition-all cursor-pointer"
            >
              {isAnalyzing ? (
                <>
                  <CircleNotch size={15} className="animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Brain size={15} weight="duotone" />
                  Analyze with AI
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Tips */}
      {!analyzed && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            'Split core vs. optional skills so the AI ranks candidates with better precision.',
            'Specify exact years of experience ranges to calibrate the trajectory predictor.',
            'Write short, clear responsibilities for clean semantic embedding matches.',
          ].map((tip, i) => (
            <div key={i} className="flex gap-3 p-4 border border-border/40 rounded-xl bg-muted/20">
              <CheckCircle size={16} weight="duotone" className="text-emerald-500 shrink-0 mt-0.5" />
              <p className="text-xs text-muted-foreground leading-relaxed">{tip}</p>
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      {analyzed && (
        <div className="animate-in fade-in slide-in-from-bottom-3 duration-400 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-foreground">Extraction Complete</h2>
              <p className="text-xs text-muted-foreground mt-0.5">AI parsed your JD into a structured ranking schema.</p>
            </div>
            <div className="flex items-center gap-1.5 text-emerald-600 text-xs font-semibold bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full">
              <CheckCircle size={13} weight="fill" />
              Ready to rank
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Required Skills */}
            <div className="bg-card border border-border/60 rounded-xl p-5 space-y-3">
              <h3 className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">Core Skills</h3>
              {requiredSkills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {requiredSkills.map((skill: string) => (
                    <span key={skill} className="text-[11px] font-semibold px-2.5 py-1 rounded-lg border border-foreground/15 bg-foreground/5 text-foreground">
                      {skill}
                    </span>
                  ))}
                </div>
              ) : <p className="text-xs text-muted-foreground">None extracted</p>}
            </div>

            {/* Optional Skills */}
            <div className="bg-card border border-border/60 rounded-xl p-5 space-y-3">
              <h3 className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">Nice-to-Have</h3>
              {optionalSkills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {optionalSkills.map((skill: string) => (
                    <span key={skill} className="text-[11px] font-semibold px-2.5 py-1 rounded-lg border border-border/50 bg-muted/40 text-muted-foreground">
                      {skill}
                    </span>
                  ))}
                </div>
              ) : <p className="text-xs text-muted-foreground">None extracted</p>}
            </div>

            {/* Insights & CTA */}
            <div className="space-y-3">
              <div className="bg-card border border-border/60 rounded-xl p-4 space-y-2.5">
                <h3 className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">AI Insights</h3>
                <div className="flex gap-2 text-xs text-amber-600 dark:text-amber-400">
                  <Warning size={15} weight="duotone" className="shrink-0 mt-px" />
                  <span>{role} is highly specialized — expect fewer top-decile candidates.</span>
                </div>
                <div className="flex gap-2 text-xs text-emerald-600 dark:text-emerald-400">
                  <CheckCircle size={15} weight="duotone" className="shrink-0 mt-px" />
                  <span>{minExp}+ year requirement aligns with parsed seniority signals.</span>
                </div>
              </div>

              <button
                onClick={() => {
                  localStorage.setItem('talentIntelAutoRunRank', 'true');
                  router.push('/rank');
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-secondary text-secondary-foreground shadow-md rounded-xl text-sm font-semibold hover:bg-secondary/90 active:scale-[0.98] transition-all cursor-pointer"
              >
                <Play size={14} weight="fill" />
                Rank Candidates
                <ArrowRight size={14} weight="bold" className="ml-auto" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
