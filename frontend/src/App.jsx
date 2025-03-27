import { useState } from "react";
// import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
// import { Card, CardContent } from "@/components/ui/card";

export default function ResumeScanner() {
  const [file, setFile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("resume", file);

    try {
      const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setJobs(data.jobs.slice(0, 50));
    } catch (error) {
      console.error("Error fetching jobs:", error);
    }
    setLoading(false);
  };

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-4">
      <h1 className="text-xl font-bold">Resume Scanner</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={loading}>
        {loading ? "Processing..." : "Upload & Scan"}
      </button>
      <div>
        <div className="p-4 space-y-2">
          <h2 className="text-lg font-semibold">Job Listings</h2>
          <ul className="list-disc pl-4">
            {jobs.length > 0 ? (
              jobs.map((job, index) => (
                <li key={index}>
                  <a href={job} target="_blank" rel="noopener noreferrer" className="text-blue-500">
                    {job}
                  </a>
                </li>
              ))
            ) : (
              <p>No jobs found.</p>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
