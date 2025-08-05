'use client';

import React from 'react';
import { HardDrive } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SystemStatsType } from '@/redux/types/monitor';
import { Skeleton } from '@/components/ui/skeleton';
import { useTranslation } from '@/hooks/use-translation';
import { Table, TableBody, TableRow, TableCell, TableHead, TableHeader } from '@/components/ui/table';

interface DiskUsageCardProps {
  systemStats: SystemStatsType | null;
}

const DiskUsageCard: React.FC<DiskUsageCardProps> = ({ systemStats }) => {
  const { t } = useTranslation();

  if (!systemStats) {
    return <DiskUsageCardSkeleton />;
  }

  const { disk } = systemStats;

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs sm:text-sm font-bold flex items-center">
          <HardDrive className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2 text-muted-foreground" />
          {t('dashboard.disk.title')}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 sm:space-y-3">
          <div className="w-full h-2 bg-gray-200 rounded-full">
            <div
              className={`h-2 rounded-full ${disk.percentage > 80 ? 'bg-destructive' : 'bg-primary'}`}
              style={{ width: `${disk.percentage}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span className="truncate max-w-[80px] sm:max-w-[100px]">
              {t('dashboard.disk.used').replace('{value}', disk.used.toFixed(2))}
            </span>
            <span className="truncate max-w-[60px] sm:max-w-[80px]">
              {t('dashboard.disk.percentage').replace('{value}', disk.percentage.toFixed(1))}
            </span>
            <span className="truncate max-w-[80px] sm:max-w-[100px]">
              {t('dashboard.disk.total').replace('{value}', disk.total.toFixed(2))}
            </span>
          </div>
          <div className="text-xs font-mono text-muted-foreground mt-1 sm:mt-2">
            <Table className="min-w-full overflow-x-hidden">
              <TableHeader>
                <TableRow>
                  <TableHead className="text-left pr-1 sm:pr-2">
                    {t('dashboard.disk.table.headers.mount')}
                  </TableHead>
                  <TableHead className="text-right pr-1 sm:pr-2">
                    {t('dashboard.disk.table.headers.size')}
                  </TableHead>
                  <TableHead className="text-right pr-1 sm:pr-2">
                    {t('dashboard.disk.table.headers.used')}
                  </TableHead>
                  <th className="text-right">{t('dashboard.disk.table.headers.percentage')}</th>
                </TableRow>
              </TableHeader>
              <TableBody>
                {disk.allMounts.map((mount, index) => (
                  <TableRow key={index} className='border-0'>
                    <TableCell>
                      {mount.mountPoint}
                    </TableCell>
                    <TableCell>
                      {mount.size}
                      </TableCell>
                    <TableCell>
                      {mount.used}
                    </TableCell>
                    <TableCell>
                      {mount.capacity}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DiskUsageCard;

const DiskUsageCardSkeleton = () => {
  const { t } = useTranslation();

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs sm:text-sm font-medium flex items-center">
          <HardDrive className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2 text-muted-foreground" />
          {t('dashboard.disk.title')}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 sm:space-y-3">
          <div className="w-full h-2 bg-gray-200 rounded-full">
            <div className="h-2 rounded-full bg-gray-400" />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-10" />
            <Skeleton className="h-3 w-20" />
          </div>
          <div className="text-xs font-mono text-muted-foreground mt-1 sm:mt-2 overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr>
                  <th className="text-left pr-1 sm:pr-2">
                    {t('dashboard.disk.table.headers.mount')}
                  </th>
                  <th className="text-right pr-1 sm:pr-2">
                    {t('dashboard.disk.table.headers.size')}
                  </th>
                  <th className="text-right pr-1 sm:pr-2">
                    {t('dashboard.disk.table.headers.used')}
                  </th>
                  <th className="text-right">{t('dashboard.disk.table.headers.percentage')}</th>
                </tr>
              </thead>
              <tbody className="text-xxs sm:text-xs">
                <tr>
                  <td className="text-left pr-1 sm:pr-2">
                    <Skeleton className="h-3 w-10" />
                  </td>
                  <td className="text-right pr-1 sm:pr-2">
                    <Skeleton className="h-3 w-10" />
                  </td>
                  <td className="text-right pr-1 sm:pr-2">
                    <Skeleton className="h-3 w-10" />
                  </td>
                  <td className="text-right">
                    <Skeleton className="h-3 w-10" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
