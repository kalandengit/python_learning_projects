export type PlanKey = "free" | "starter" | "pro" | "business" | "enterprise";

export type PlanLimit = {
  name: string;
  monthlyDocuments: number;
  monthlyUploads: number;
  storageMb: number;
  seats: number;
  priceMonthlyUsd: number;
  stripePriceEnv?: string;
};

export const PLAN_LIMITS: Record<PlanKey, PlanLimit> = {
  free: { name: "Free", monthlyDocuments: 5, monthlyUploads: 10, storageMb: 100, seats: 1, priceMonthlyUsd: 0 },
  starter: { name: "Starter", monthlyDocuments: 50, monthlyUploads: 100, storageMb: 1024, seats: 3, priceMonthlyUsd: 19, stripePriceEnv: "STRIPE_PRICE_STARTER_MONTHLY" },
  pro: { name: "Pro", monthlyDocuments: 250, monthlyUploads: 500, storageMb: 10240, seats: 10, priceMonthlyUsd: 49, stripePriceEnv: "STRIPE_PRICE_PRO_MONTHLY" },
  business: { name: "Business", monthlyDocuments: 1000, monthlyUploads: 2000, storageMb: 102400, seats: 25, priceMonthlyUsd: 149, stripePriceEnv: "STRIPE_PRICE_BUSINESS_MONTHLY" },
  enterprise: { name: "Enterprise", monthlyDocuments: Number.MAX_SAFE_INTEGER, monthlyUploads: Number.MAX_SAFE_INTEGER, storageMb: Number.MAX_SAFE_INTEGER, seats: Number.MAX_SAFE_INTEGER, priceMonthlyUsd: 0 }
};

export function getPlanLimit(plan: string | null | undefined): PlanLimit {
  return PLAN_LIMITS[(plan as PlanKey) || "free"] ?? PLAN_LIMITS.free;
}

export function getStripePriceId(plan: PlanKey) {
  const envName = PLAN_LIMITS[plan].stripePriceEnv;
  return envName ? process.env[envName] : undefined;
}

export const PAID_PLANS: PlanKey[] = ["starter", "pro", "business"];
