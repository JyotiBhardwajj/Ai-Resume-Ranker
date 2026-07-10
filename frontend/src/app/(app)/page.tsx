'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  UploadSimple,
  FileText,
  Trophy,
  Lightning,
  Brain,
  Scales,
  ArrowRight,
} from '@phosphor-icons/react';

import { InteractiveHoverButton } from '@/components/ui/interactive-hover-button';
import { DotPattern } from '@/components/ui/dot-pattern';
import { Marquee } from '@/components/ui/marquee';
import { BlurFade } from '@/components/ui/blur-fade';
import { AnimatedShinyText } from '@/components/ui/animated-shiny-text';
import { RetroGrid } from '@/components/ui/retro-grid';
import { MagicCard } from '@/components/ui/magic-card';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

const features = [
  {
    tag: 'PARSE',
    title: 'Resume parsing',
    description: 'Raw resumes become structured candidate profiles in seconds. No manual data entry.',
    icon: UploadSimple,
    span: 'md:col-span-2 md:row-span-1',
    upcoming: true,
  },
  {
    tag: 'ANALYZE',
    title: 'Job description analysis',
    description: 'We read seniority, domain, and hidden requirements most ATS tools miss.',
    icon: FileText,
    span: 'md:col-span-1 md:row-span-2',
  },
  {
    tag: 'RANK',
    title: 'Candidate ranking',
    description: 'Semantic matching ranks by real capability, not keyword density.',
    icon: Trophy,
    span: 'md:col-span-1 md:row-span-1',
  },
  {
    tag: 'EXPLAIN',
    title: 'Match reasoning',
    description: 'Every recommendation comes with a clear breakdown of why.',
    icon: Lightning,
    span: 'md:col-span-1 md:row-span-1',
  },
  {
    tag: 'PREP',
    title: 'Interview copilot',
    description: 'Tailored interview guides built around each candidate\'s gaps.',
    icon: Brain,
    span: 'md:col-span-1 md:row-span-1',
  },
  {
    tag: 'COMPARE',
    title: 'Risk profiling',
    description: 'Flight risk, overqualification, and gaps flagged automatically.',
    icon: Scales,
    span: 'md:col-span-2 md:row-span-1',
  },
];

const integrations = [
  'Golang', 'React', 'Python', 'Next.js', 'Supabase', 'PostgreSQL',
  'FastAPI', 'TailwindCSS', 'TypeScript', 'Vector DB',
];

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground overflow-hidden">
      {/* HERO */}
      <section className="relative flex flex-col items-center justify-center text-center px-6 pt-32 pb-24 min-h-[90vh]">
        <DotPattern
          className="absolute inset-0 [mask-image:radial-gradient(420px_circle_at_center,white,transparent)] opacity-40"
          width={24}
          height={24}
        />

        <BlurFade delay={0.05}>
          <div className="group relative mb-8 inline-flex items-center rounded-full border border-border/60 bg-card/50 px-4 py-1.5 backdrop-blur-md">
            <AnimatedShinyText className="text-xs font-mono uppercase tracking-widest">
              AI Recruiting, Reasoned
            </AnimatedShinyText>
          </div>
        </BlurFade>

        <BlurFade delay={0.15}>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight max-w-3xl leading-[1.05]">
            Hire on signal, not resumes.
          </h1>
        </BlurFade>

        <BlurFade delay={0.25}>
          <p className="mt-5 text-base md:text-lg text-muted-foreground max-w-md">
            Explainable AI ranking for serious talent teams.
          </p>
        </BlurFade>

        <BlurFade delay={0.35}>
          <div className="mt-10 relative">
            <Link href="/jd-analysis">
              <InteractiveHoverButton className="px-8 py-4 font-semibold text-lg">
                Get started
              </InteractiveHoverButton>
            </Link>
          </div>
        </BlurFade>
      </section>

      {/* MARQUEE */}
      <section className="border-y border-border/40 bg-card/30 py-6 relative">
        <Marquee className="[--duration:30s]" pauseOnHover>
          {integrations.map((tech) => (
            <span
              key={tech}
              className="font-mono text-xs uppercase tracking-widest text-muted-foreground/60 mx-8"
            >
              {tech}
            </span>
          ))}
        </Marquee>
      </section>

      {/* FEATURES — BENTO GRID */}
      <section className="py-28 md:py-36 px-6">
        <div className="container mx-auto max-w-5xl">
          <BlurFade>
            <h2 className="text-2xl md:text-3xl font-semibold tracking-tight mb-12 max-w-md">
              One pipeline, six decisions made for you.
            </h2>
          </BlurFade>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 auto-rows-[minmax(200px,auto)]">
            {features.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <BlurFade key={feature.title} delay={0.05 * idx} inView className={feature.span}>
                  <MagicCard
                    mode="orb"
                    glowFrom="#2EE6D6"
                    glowTo="#6b21ef"
                    className="group relative h-full flex flex-col justify-between overflow-hidden rounded-2xl border border-border/50 bg-card p-6"
                  >
                    <div className="flex items-center justify-between mb-8">
                      <span className="font-mono text-[10px] tracking-[0.2em] text-primary uppercase">
                        {feature.tag}
                      </span>
                      <Icon size={18} weight="bold" className="text-muted-foreground/50 group-hover:text-primary transition-colors" />
                      {feature.upcoming && (
                        <span className="absolute top-4 right-4 font-mono text-[9px] uppercase tracking-widest text-muted-foreground/40">
                          soon
                        </span>
                      )}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold mb-1.5">{feature.title}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </MagicCard>
                </BlurFade>
              );
            })}
          </div>
        </div>
      </section>

      {/* FAQ SECTION */}
      <section className="py-24 px-6 border-t border-border/40">
        <div className="container mx-auto max-w-3xl">
          <BlurFade delay={0.1} inView>
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-12 text-center">
              Frequently Asked Questions
            </h2>
          </BlurFade>

          <BlurFade delay={0.2} inView>
            <Accordion className="w-full space-y-4">
              <AccordionItem value="item-1" className="border border-border/50 bg-card px-6 rounded-2xl shadow-sm data-open:shadow-md transition-all">
                <AccordionTrigger className="hover:no-underline py-6 text-left font-semibold">
                  How does the semantic parsing differ from standard keyword matching?
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground leading-relaxed pb-6 text-sm">
                  Traditional ATS systems look for exact keyword matches. Our AI understands the context of the entire resume. For example, if a job requires &quot;React&quot;, it knows that a candidate with &quot;Next.js&quot; and &quot;Redux&quot; experience has the necessary underlying skills, even if the exact keyword &quot;React&quot; is missing.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="item-2" className="border border-border/50 bg-card px-6 rounded-2xl shadow-sm data-open:shadow-md transition-all">
                <AccordionTrigger className="hover:no-underline py-6 text-left font-semibold">
                  Can it detect hidden potential or &quot;flight risks&quot;?
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground leading-relaxed pb-6 text-sm">
                  Yes. Our risk profiling engine analyzes career trajectories to flag candidates who might be overqualified or have a history of very short tenures. It also highlights &quot;hidden gems&quot;&mdash;candidates with unconventional backgrounds who exhibit strong foundational skills.
                </AccordionContent>
              </AccordionItem>
              <AccordionItem value="item-3" className="border border-border/50 bg-card px-6 rounded-2xl shadow-sm data-open:shadow-md transition-all">
                <AccordionTrigger className="hover:no-underline py-6 text-left font-semibold">
                  How does the Interview Copilot work?
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground leading-relaxed pb-6 text-sm">
                  Based on the candidate&apos;s specific gaps identified during the parsing stage, the Copilot generates tailored technical and behavioral questions. This ensures your interview process directly addresses the areas where the candidate needs the most scrutiny.
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </BlurFade>
        </div>
      </section>

      {/* CTA SECTION */}
      <section className="relative flex flex-col items-center justify-center text-center px-6 py-32 overflow-hidden border-t border-border/40">
        <RetroGrid className="opacity-50" />

        <BlurFade delay={0.1} inView>
          <h2 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
            Ready to upgrade your hiring?
          </h2>
        </BlurFade>

        <BlurFade delay={0.2} inView>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto mb-10">
            Stop guessing who the best candidate is. Let our semantic engine do the heavy lifting for you.
          </p>
        </BlurFade>

        <BlurFade delay={0.3} inView>
          <Link href="/jd-analysis" className="relative inline-flex z-10">
            <InteractiveHoverButton
              className="px-10 py-4 font-semibold"
            >
              Start ranking candidates
            </InteractiveHoverButton>
          </Link>
        </BlurFade>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-border/40 py-10 px-6">
        <div className="container mx-auto max-w-5xl flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" weight="bold" />
            <span className="font-semibold text-sm">TalentIntel</span>
          </div>
          <p className="font-mono text-xs text-muted-foreground/50 uppercase tracking-widest">
            © 2026 — AI Recruiter Challenge
          </p>
        </div>
      </footer>
    </div>
  );
}