import PageHeader from "@/components/PageHeader";
import DemandsTable from "@/components/DemandsTable";
import { getDemands } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DemandsPage() {
  const demands = await getDemands();

  return (
    <>
      <PageHeader title="Demand Feed" subtitle="需求信号流" />
      <DemandsTable demands={demands} />
    </>
  );
}
