import { cache } from "react";
import { supabase } from "@/lib/supabase";

// Направление литовской программы по классификатору общего приёма LAMA BPO
// (таблица lt_programme_field, её пишет pipeline/src/lt_load_fields.py).
// Названия — только литовские: так они стоят в официальном списке, мы их не
// переводим.

export type LtProgrammeField = {
  /** Группа направлений: «Inžinerijos mokslai». */
  groupName: string;
  /** Код направления: «E14». */
  fieldCode: string;
  /** Направление: «Aeronautikos inžinerija». */
  fieldName: string;
};

export const getLtProgrammeField = cache(async (programmeId: string): Promise<LtProgrammeField | null> => {
  const { data, error } = await supabase
    .from("lt_programme_field")
    .select("group_name, field_code, field_name")
    .eq("programme_id", programmeId)
    .maybeSingle();

  if (error) throw error;
  if (!data) return null;
  return { groupName: data.group_name, fieldCode: data.field_code, fieldName: data.field_name };
});
