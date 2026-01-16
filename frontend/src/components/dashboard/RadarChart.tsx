import { Radar, RadarChart as RechartsRadar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend } from 'recharts';

interface RadarChartProps {
  data: {
    category: string;
    user: number;
    ideal: number;
  }[];
}

export const RadarChartComponent = ({ data }: RadarChartProps) => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <RechartsRadar data={data}>
        <PolarGrid stroke="#E5E7EB" />
        <PolarAngleAxis dataKey="category" tick={{ fill: '#1E293B', fontSize: 12 }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#6B7280' }} />
        <Radar
          name="Your Performance"
          dataKey="user"
          stroke="#3B82F6"
          fill="#3B82F6"
          fillOpacity={0.6}
        />
        <Radar
          name="Ideal Candidate"
          dataKey="ideal"
          stroke="#10B981"
          fill="#10B981"
          fillOpacity={0.3}
        />
        <Legend />
      </RechartsRadar>
    </ResponsiveContainer>
  );
};
