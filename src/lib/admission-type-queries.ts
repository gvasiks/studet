import { cache } from "react";
import { supabase } from "@/lib/supabase";

export type SelectionType = "competitive_score" | "entrance_exam" | "open_admission" | "interview";

export type AdmissionTypeRecord = {
  selectionType: SelectionType;
};

// Гейт на verified_at в самом запросе — тот же паттерн, что и
// getFormula()/getApplicationRounds(). Дублируется RLS-политикой
// university_admission_type_public_read (supabase/migrations/
// 20260917205948_university_admission_type.sql).
export const getAdmissionType = cache(
  async (universityId: string): Promise<AdmissionTypeRecord | null> => {
    const { data, error } = await supabase
      .from("university_admission_type")
      .select("selection_type")
      .eq("university_id", universityId)
      .not("verified_at", "is", null)
      .maybeSingle();

    if (error) throw error;
    if (!data) return null;

    return { selectionType: data.selection_type as SelectionType };
  },
);
