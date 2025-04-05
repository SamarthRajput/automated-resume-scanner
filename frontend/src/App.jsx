import React, { useState, useRef, useEffect } from 'react';

const ResumeScanner = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const resultsEndRef = useRef(null);

  useEffect(() => {
    if (loadingMore && resultsEndRef.current) {
      resultsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [data?.jobs?.length]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    const validTypes = ['application/pdf', 
                       'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(selectedFile.type)) {
      setError('Please upload a PDF or DOCX file');
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setError('File size exceeds 5MB limit');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setData(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('resume', file);

    try {
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to process resume');
      }

      setData(result);
    } catch (err) {
      setError(err.message);
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadMoreJobs = async () => {
    if (!data?.skills || loadingMore) return;

    setLoadingMore(true);
    try {
      const response = await fetch(
        `http://localhost:5000/jobs?skills=${data.skills.join(',')}&page=${data.next_page}`
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to load more jobs');
      }

      setData(prev => ({
        ...prev,
        jobs: [...prev.jobs, ...result.jobs],
        next_page: result.next_page
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <div className="card resume-scanner">
      <h1>India Job Finder</h1>
      
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".pdf,.docx"
        disabled={loading}
        className="file-input"
      />
      <button
        onClick={handleUpload}
        disabled={!file || loading}
      >
        {loading ? 'Processing...' : 'Scan Resume'}
      </button>

      {error && <p className="error">{error}</p>}

      {data && (
        <div className="results">
          <div>
            <h2>Your Information</h2>
            <p><strong>Email:</strong> {data.contact.email || 'Not found'}</p>
            <p><strong>Phone:</strong>  {data.contact.phone || 'Not found'}</p>
          </div>

          <div>
            <h2>Skills</h2>
            <div className="skills-container">
              {data.skills.length > 0 ? (
                data.skills.map((skill, index) => (
                  <span key={index} className="skill-tag">{skill}</span>
                ))
              ) : (
                <p>No skills detected</p>
              )}
            </div>
          </div>

          <div>
            <h2>Matching Jobs in India</h2>
            {data.jobs.length > 0 ? (
              <>
                <div className="jobs-grid">
                  {data.jobs.map((job, index) => (
                    <div key={index} className="job-card">
                      <h3>{job.title}</h3>
                      <p className="job-company">{job.company}</p>
                      <p className="job-location">{job.location}</p>
                      <a 
                        href={job.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="job-link"
                      >
                        View Job
                      </a>
                    </div>
                  ))}
                </div>
                <div ref={resultsEndRef} />
                <button
                  onClick={loadMoreJobs}
                  disabled={loadingMore}
                  className="load-more"
                >
                  {loadingMore ? 'Loading...' :  'Load More Jobs'}
                </button>
              </>
            ) :  (
              <p>No jobs found for your skills</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeScanner;