export default function FiltersBar({ value, onChange }) {
  return (
    <div className="filters-bar">
      <label className="field-label" htmlFor="filter">
        View Focus
      </label>
      <select id="filter" value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="overall">Overall</option>
        <option value="sales">Sales</option>
        <option value="seasonality">Seasonality</option>
        <option value="operations">Operations</option>
      </select>
    </div>
  );
}
