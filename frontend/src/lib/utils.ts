import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function sourceKey(sensorType: string, sourceFile: string) {
  return `${sensorType}::${sourceFile}`;
}
