import { generateDocumentationFromImage } from "@/lib/ai/generate-document";
import { NextResponse } from "next/server";
import { z } from "zod";

const bodySchema = z.object({ imageUrl: z.string().url(), context: z.string().optional() });

export async function POST(request: Request) {
  try {
    const body = bodySchema.parse(await request.json());
    const document = await generateDocumentationFromImage({ imageUrl: body.imageUrl, userContext: body.context });
    return NextResponse.json({ document });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Unknown error" }, { status: 400 });
  }
}
