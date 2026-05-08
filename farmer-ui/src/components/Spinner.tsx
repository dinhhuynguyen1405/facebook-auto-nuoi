import { cn } from "@/lib/utils";
export function Spinner({ className }: { className?: string }) {
  return (
    <div className={cn("w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin", className)} />
  );
}
export function PageLoader() {
  return (
    <div className="flex-1 flex items-center justify-center min-h-64">
      <Spinner className="w-8 h-8" />
    </div>
  );
}
