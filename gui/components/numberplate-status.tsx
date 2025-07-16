"use client";

import { useNumberPlate } from "./numberplate-context";

export default function NumberPlateStatus() {
  const { currentNumber, connectionStatus, lastUpdate } = useNumberPlate();

  return (
    <div className="bg-white rounded-lg shadow-md p-4 max-w-sm">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">
        Number Plate Status
      </h3>
      
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-gray-600">Connection:</span>
          <span className={`font-medium ${
            connectionStatus === "Connected" 
              ? "text-green-600" 
              : connectionStatus === "Error"
              ? "text-red-600"
              : "text-gray-600"
          }`}>
            {connectionStatus}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600">Current Number:</span>
          <span className="font-medium text-indigo-600">
            {currentNumber !== null ? currentNumber : "None"}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600">Last Update:</span>
          <span className="font-medium text-gray-800">
            {lastUpdate || "Never"}
          </span>
        </div>
      </div>
    </div>
  );
}
