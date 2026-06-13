export default function PassportPage({ params }: { params: { id: string } }) {
  return <div className="p-8">Digital Product Passport for ID: {params.id} (P2-C2)</div>;
}
