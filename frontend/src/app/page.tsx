import { getUniverse } from "@/lib/api";
import { ConvictionBoard } from "@/components/ConvictionBoard";
import { ApiDown } from "@/components/ApiDown";

export const dynamic = "force-dynamic";

export default async function Dashboard() {
  const universe = await getUniverse();
  if (!universe) return <ApiDown />;
  return <ConvictionBoard universe={universe} />;
}
