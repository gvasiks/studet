// Источник — view pipeline_health (миграция 20260922090000): узкая сводка,
// читается анонимным ключом, сама таблица pipeline_run — нет (тот же приём,
// что у verification_queue: RLS закрыт, view создан ролью миграции и
// обходит его).
import { cache } from "react";
import { supabase } from "@/lib/supabase";
import type { PipelineHealth } from "@/lib/pipeline-health";

export const getPipelineHealth = cache(async (): Promise<PipelineHealth> => {
  const { data, error } = await supabase.from("pipeline_health").select("*").maybeSingle();
  if (error) throw error;

  return {
    lastSuccessAt: data?.last_success_at ?? null,
    lastStatus: data?.last_status ?? null,
    lastFinishedAt: data?.last_finished_at ?? null,
    lastErrorCount: data?.last_error_count ?? null,
  };
});
