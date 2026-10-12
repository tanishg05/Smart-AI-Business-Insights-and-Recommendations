export default function RecommendationCard({ title, description }) {
  return (
    <div className="recommendation-card">
      <h4>{title}</h4>
      <p>{description}</p>
    </div>
  );
}
