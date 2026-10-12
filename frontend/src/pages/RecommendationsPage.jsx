import RecommendationCard from '../components/RecommendationCard';

/** Rule-based recommendations; rendered inside the Intelligence Hub. */
export default function RecommendationsPage({ data }) {
  const recommendations = data?.recommendations || [];
  return (
    <div className="rec-grid">
      {recommendations.map((item) => (
        <RecommendationCard key={item.title} {...item} />
      ))}
    </div>
  );
}
