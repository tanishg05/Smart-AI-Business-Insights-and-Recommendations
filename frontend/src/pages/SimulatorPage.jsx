import ScenarioSimulator from '../components/ScenarioSimulator';

export default function SimulatorPage({ filters }) {
  return (
    <div className="view">
      <ScenarioSimulator filters={filters} />
    </div>
  );
}
