import React from "react";
import FinbotMediumImage from "assets/finbot_medium.png";

import { Link } from "react-router-dom";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "components/ui/card";

export interface WelcomeProps {}

export const Welcome: React.FC<WelcomeProps> = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Welcome to finbot!</h1>
      <div className="flex gap-6">
        <div className="w-40 shrink-0">
          <img src={FinbotMediumImage} alt="finbot" className="w-full" />
        </div>
        <Card className="max-w-lg">
          <CardHeader>
            <CardTitle>First steps</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p>
              <strong>Finbot</strong> is your personal finance assistant, it
              automatically gathers financial information from your personal
              accounts and displays them on your dashboard.
            </p>
            <p>
              To <strong>get started with finbot</strong>, you need to{" "}
              <Link
                to="/settings/linked"
                className="text-primary underline underline-offset-4 hover:text-primary/80"
              >
                link at least one account
              </Link>
              .
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
