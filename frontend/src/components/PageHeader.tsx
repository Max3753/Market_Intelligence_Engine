interface PageHeaderProps {
  title: string;
  subtitle?: string;
}

export default function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <div className="mb-8">
      <h1 className="bg-gradient-to-r from-white via-white to-slate-400 bg-clip-text text-2xl font-bold tracking-tight text-transparent">
        {title}
      </h1>
      {subtitle && (
        <p className="mt-1.5 text-sm text-slate-400">{subtitle}</p>
      )}
      <div className="mt-4 h-px w-full bg-gradient-to-r from-sky-400/30 via-white/10 to-transparent" />
    </div>
  );
}
