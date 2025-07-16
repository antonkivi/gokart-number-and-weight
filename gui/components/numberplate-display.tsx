"use client";

import { useNumberPlate } from "./numberplate-context";
interface NumberPlateDisplayProps {
    className?: string;
}
export default function NumberPlateDisplay({ className }: NumberPlateDisplayProps) {
    const { currentNumber } = useNumberPlate();

    return (
        <span className={`${className}`}>
            {currentNumber !== null ? currentNumber : "--"}
        </span>
    );
}
