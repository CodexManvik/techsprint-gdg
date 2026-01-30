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
        <PolarGrid stroke="rgba(255,255,255,0.1)" />
        <PolarAngleAxis
          dataKey="category"
          tick={{ fill: 'hsl(var(--foreground-muted))', fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: 'hsl(var(--foreground-muted))' }}
          stroke="rgba(255,255,255,0.1)"
        />
        <Radar
          name="Your Performance"
          dataKey="user"
          stroke="#7c3aed"
          fill="url(#userGradient)"
          fillOpacity={0.6}
          strokeWidth={2}
        />
        <Radar
          name="Ideal Candidate"
          dataKey="ideal"
          stroke="#22c55e"
          fill="url(#idealGradient)"
          fillOpacity={0.3}
          strokeWidth={2}
        />
        <Legend
          wrapperStyle={{
            paddingTop: '20px',
            color: 'hsl(var(--foreground-muted))'
          }}
        />
        <defs>
          <linearGradient id="userGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3a0ca3" stopOpacity={0.8} />
            <stop offset="100%" stopColor="#7c3aed" stopOpacity={0.3} />
          </linearGradient>
          <linearGradient id="idealGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22c55e" stopOpacity={0.5} />
            <stop offset="100%" stopColor="#22c55e" stopOpacity={0.1} />
          </linearGradient>
        </defs>
      </RechartsRadar>
    </ResponsiveContainer>
  );
};
