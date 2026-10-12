import SectionCard from '../components/SectionCard';
import RecommendationCard from '../components/RecommendationCard';

export default function RecommendationsPage({ data }) {
  const recommendations = data?.recommendations || [];

  return (
    <SectionCard title="Strategic Recommendations" subtitle="Actions to improve performance">
      <div className="cards-grid">
        {recommendations.map((item) => (
          <RecommendationCard key={item.title} title={item.title} description={item.description} />
        ))}
      </div>
    </SectionCard>
  );
}
