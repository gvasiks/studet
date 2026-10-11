import { cache } from "react";
import { supabase } from "@/lib/supabase";

// Направление эстонской программы по классификатору ISCED-F (таблица
// ee_programme_field, её пишет pipeline/src/ee_load_fields.py). Названия —
// только эстонские: так они стоят на государственном портале, мы их не
// переводим.

export type EeProgrammeField = {
  /** Область: «Ärindus, haldus ja õigus». */
  broadName: string;
  /** Направление: «Õigus». */
  fieldName: string;
};

export const getEeProgrammeField = cache(async (programmeId: string): Promise<EeProgrammeField | null> => {
  const { data, error } = await supabase
    .from("ee_programme_field")
    .select("broad_name, field_name")
    .eq("programme_id", programmeId)
    .maybeSingle();

  if (error) throw error;
  if (!data) return null;
  return { broadName: data.broad_name, fieldName: data.field_name };
});
