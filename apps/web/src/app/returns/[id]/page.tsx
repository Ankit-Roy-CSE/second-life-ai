export default function ReturnDetailsPage({ params }: { params: { id: string } }) {
  return <div className="p-8">Return Status / Grading for ID: {params.id}</div>;
}
