'use client';
import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { PreferenceType } from '@/redux/types/notification';

export interface NotificationPreferenceCardProps {
  title: string;
  description: string;
  preferences?: PreferenceType[];
  onUpdate: (id: string, enabled: boolean) => void;
}

const NotificationPreferenceCard: React.FC<NotificationPreferenceCardProps> = ({
  title,
  description,
  preferences,
  onUpdate
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {preferences?.map((pref) => (
          <div className="flex items-center justify-between" key={pref.id}>
            <div className="space-y-0.5">
              <Label htmlFor={pref.id} className="text-base">
                {pref.label}
              </Label>
              <p className="text-sm text-muted-foreground">{pref.description}</p>
            </div>
            <Switch
              id={pref.id}
              defaultChecked={pref.enabled}
              onCheckedChange={(enabled) => onUpdate?.(pref.id, enabled)}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

export default NotificationPreferenceCard;
