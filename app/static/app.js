// CertiForge Frontend Application Controller
document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const navButtons = document.querySelectorAll('.nav-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');
  const subnavButtons = document.querySelectorAll('.subnav-btn');
  const subtabPanes = document.querySelectorAll('.subtab-pane');
  
  // Forms & Inputs
  const form = document.getElementById('create-job-form');
  const eventNameInput = document.getElementById('event_name');
  const certTitleInput = document.getElementById('title');
  const issueDateInput = document.getElementById('issue_date');
  const issuerNameInput = document.getElementById('issuer_name');
  const issuerTitleInput = document.getElementById('issuer_title');
  const recipientsJsonArea = document.getElementById('recipients_json');
  const processSyncCheck = document.getElementById('process_sync');
  
  // Mockup elements
  const mockTitle = document.getElementById('mock-title');
  const mockEvent = document.getElementById('mock-event');
  const mockIssuer = document.getElementById('mock-issuer');
  const mockTitleSub = document.getElementById('mock-title-sub');
  
  // Sample buttons
  const btnLoadSample = document.getElementById('btn-load-sample');
  const btnLoadFaultDemo = document.getElementById('btn-load-fault-demo');
  
  // CSV dropzone
  const csvDropzone = document.getElementById('csv-dropzone');
  const csvFileInput = document.getElementById('csv_file_input');
  const csvFilenameDisplay = document.getElementById('csv-filename');
  let selectedCsvFile = null;
  
  // Monitor elements
  const monitorTabBtn = document.getElementById('monitor-nav-btn');
  const jobStatusBanner = document.getElementById('job-status-banner');
  const bannerStatusBadge = document.getElementById('banner-status-badge');
  const bannerJobTitle = document.getElementById('banner-job-title');
  const bannerJobId = document.getElementById('banner-job-id');
  const bannerProgressFill = document.getElementById('banner-progress-fill');
  const bannerProgressText = document.getElementById('banner-progress-text');
  const bannerLiveIndicator = document.getElementById('banner-live-indicator');
  const metricTotal = document.getElementById('metric-total');
  const metricProcessed = document.getElementById('metric-processed');
  const metricSuccess = document.getElementById('metric-success');
  const metricFailed = document.getElementById('metric-failed');
  const recipientsTableCard = document.getElementById('recipients-table-card');
  const recipientsTbody = document.getElementById('recipients-tbody');
  const monitorActionsBar = document.getElementById('monitor-actions-bar');
  const btnDownloadZipPdf = document.getElementById('btn-download-zip-pdf');
  const btnDownloadZipPng = document.getElementById('btn-download-zip-png');
  const btnRefreshJob = document.getElementById('btn-refresh-job');
  const jobsHistoryTbody = document.getElementById('jobs-history-tbody');
  const btnRefreshHistory = document.getElementById('btn-refresh-history');
  
  // Modal elements
  const modal = document.getElementById('preview-modal');
  const modalClose = document.getElementById('modal-close');
  const modalImg = document.getElementById('modal-img');
  const modalLoading = document.getElementById('modal-loading');
  const modalDownloadPdf = document.getElementById('modal-download-pdf');
  const modalDownloadPng = document.getElementById('modal-download-png');
  
  // Verify elements
  const verifyInput = document.getElementById('verify-input');
  const btnDoVerify = document.getElementById('btn-do-verify');
  const verifyResultCard = document.getElementById('verify-result-card');
  const verifyBanner = document.getElementById('verify-banner');
  const verifyIcon = document.getElementById('verify-icon');
  const verifyHeading = document.getElementById('verify-status-heading');
  const verifySub = document.getElementById('verify-status-sub');
  
  let currentActiveJobId = null;
  let pollInterval = null;
  let allRecipientsCache = [];

  // Default date to today
  if (!issueDateInput.value) {
    issueDateInput.value = new Date().toISOString().split('T')[0];
  }

  // Live mockup synchronizer
  function updateMockup() {
    mockTitle.textContent = (certTitleInput.value || 'CERTIFICATE OF COMPLETION').toUpperCase();
    mockEvent.textContent = eventNameInput.value || 'Specialized Training Program';
    mockIssuer.textContent = issuerNameInput.value || 'Authorized Signatory';
    mockTitleSub.textContent = issuerTitleInput.value || 'Director';
  }

  [eventNameInput, certTitleInput, issuerNameInput, issuerTitleInput].forEach(inp => {
    inp.addEventListener('input', updateMockup);
  });
  updateMockup();

  // Tab switching
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      navButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(target).classList.add('active');
      if (target === 'monitor-tab') {
        loadJobsHistory();
      }
    });
  });

  // Subtab switching (JSON vs CSV)
  subnavButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.subtab;
      subnavButtons.forEach(b => b.classList.remove('active'));
      subtabPanes.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(target).classList.add('active');
    });
  });

  // Sample Batches
  const sampleCleanBatch = [
    { name: "Sophia Reynolds", email: "sophia.reynolds@example.com", custom_attributes: { grade: "Distinction", score: "99%", hours: 40 } },
    { name: "Marcus Chen", email: "marcus.chen@example.com", custom_attributes: { grade: "Honors", score: "94%", hours: 40 } },
    { name: "Amara Okafor", email: "amara.okafor@example.com", custom_attributes: { grade: "Distinction", score: "97%", hours: 40 } },
    { name: "Liam Gallagher", email: "liam.g@example.com", custom_attributes: { grade: "Pass", score: "88%", hours: 40 } },
    { name: "Elena Rostova", email: "elena.rostova@example.com", custom_attributes: { grade: "Distinction", score: "100%", hours: 40 } }
  ];

  const sampleFaultDemoBatch = [
    { name: "Alexander Hamilton", email: "alex@treasury.gov", custom_attributes: { rank: "High Distinction" } },
    { name: "   ", email: "ghost@example.com", custom_attributes: { note: "Invalid blank recipient name to test fault isolation" } },
    { name: "Benjamin Franklin", email: "benjamin@philadelphia.org", custom_attributes: { rank: "Founding Scholar" } },
    { name: "John Adams", email: "invalid-email-address", custom_attributes: { note: "Malformed email test" } },
    { name: "Thomas Jefferson", email: "thomas@virginia.edu", custom_attributes: { rank: "Distinction" } }
  ];

  btnLoadSample.addEventListener('click', () => {
    recipientsJsonArea.value = JSON.stringify(sampleCleanBatch, null, 2);
    // Switch to JSON tab
    document.querySelector('[data-subtab="json-input-pane"]').click();
  });

  btnLoadFaultDemo.addEventListener('click', () => {
    recipientsJsonArea.value = JSON.stringify(sampleFaultDemoBatch, null, 2);
    document.querySelector('[data-subtab="json-input-pane"]').click();
  });

  // Populate clean batch on initial load
  btnLoadSample.click();

  // CSV Drag & Drop
  csvDropzone.addEventListener('click', () => csvFileInput.click());
  csvDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    csvDropzone.classList.add('dragover');
  });
  csvDropzone.addEventListener('dragleave', () => csvDropzone.classList.remove('dragover'));
  csvDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    csvDropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleCsvFile(e.dataTransfer.files[0]);
    }
  });

  csvFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleCsvFile(e.target.files[0]);
    }
  });

  function handleCsvFile(file) {
    if (!file.name.endsWith('.csv')) {
      alert('Please upload a valid .csv file.');
      return;
    }
    selectedCsvFile = file;
    csvFilenameDisplay.textContent = `Selected: ${file.name} (${Math.round(file.size / 1024)} KB)`;
  }

  // Submit Job
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('submit-job-btn');
    const spinner = submitBtn.querySelector('.spinner');
    const btnText = submitBtn.querySelector('.btn-text');
    
    submitBtn.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.textContent = 'Submitting Job...';

    try {
      const activeSubtab = document.querySelector('.subtab-pane.active').id;
      const isSync = processSyncCheck.checked;
      let createdJobId = null;

      if (activeSubtab === 'csv-input-pane') {
        if (!selectedCsvFile) {
          throw new Error('Please select or drop a CSV file first.');
        }
        const formData = new FormData();
        formData.append('file', selectedCsvFile);
        formData.append('event_name', eventNameInput.value.trim());
        formData.append('issuer_name', issuerNameInput.value.trim());
        formData.append('title', certTitleInput.value.trim());
        formData.append('issue_date', issueDateInput.value);
        formData.append('issuer_title', issuerTitleInput.value.trim());
        formData.append('template_style', document.querySelector('input[name="template_style"]:checked').value);
        formData.append('process_sync', isSync);

        const res = await fetch(`/api/v1/jobs/upload-csv`, {
          method: 'POST',
          body: formData
        });
        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || 'Failed to submit CSV job');
        }
        const data = await res.json();
        createdJobId = data.job_id;

      } else {
        // JSON mode
        let recipients = [];
        try {
          recipients = JSON.parse(recipientsJsonArea.value.trim());
        } catch (jsonErr) {
          throw new Error('Invalid JSON format in recipients array: ' + jsonErr.message);
        }

        if (!Array.isArray(recipients) || recipients.length === 0) {
          throw new Error('Recipients must be a non-empty array of objects.');
        }

        const payload = {
          title: certTitleInput.value.trim(),
          event_name: eventNameInput.value.trim(),
          issue_date: issueDateInput.value,
          issuer_name: issuerNameInput.value.trim(),
          issuer_title: issuerTitleInput.value.trim(),
          template_style: document.querySelector('input[name="template_style"]:checked').value,
          recipients: recipients
        };

        const res = await fetch(`/api/v1/jobs?process_sync=${isSync}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          const errData = await res.json();
          const detail = typeof errData.detail === 'object' ? JSON.stringify(errData.detail) : errData.detail;
          throw new Error(detail || 'Failed to create job');
        }

        const data = await res.json();
        createdJobId = data.job_id;
      }

      // Switch to Monitor Tab and track progress
      monitorTabBtn.click();
      trackJob(createdJobId);

    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      submitBtn.disabled = false;
      spinner.style.display = 'none';
      btnText.textContent = 'Generate Certificates in Bulk';
    }
  });

  // Track Job function
  async function trackJob(jobId) {
    currentActiveJobId = jobId;
    if (pollInterval) clearInterval(pollInterval);

    jobStatusBanner.style.display = 'block';
    recipientsTableCard.style.display = 'block';
    monitorActionsBar.style.display = 'flex';

    await fetchAndRenderJob(jobId);

    // Poll every 1 second while in progress
    pollInterval = setInterval(async () => {
      const isFinished = await fetchAndRenderJob(jobId);
      if (isFinished) {
        clearInterval(pollInterval);
        pollInterval = null;
        loadJobsHistory();
      }
    }, 1000);
  }

  async function fetchAndRenderJob(jobId) {
    try {
      const res = await fetch(`/api/v1/jobs/${jobId}`);
      if (!res.ok) return true; // Stop polling on error
      const job = await res.json();

      allRecipientsCache = job.recipients || [];

      // Update banner info
      bannerJobTitle.textContent = `${job.event_name} (${job.title})`;
      bannerJobId.textContent = `Job ID: ${job.id}`;
      
      // Status badge
      bannerStatusBadge.textContent = job.status;
      bannerStatusBadge.className = 'status-badge ' + getStatusBadgeClass(job.status);

      // Progress bar & metrics
      const pct = job.progress_percentage || 0;
      bannerProgressFill.style.width = `${pct}%`;
      bannerProgressText.textContent = `${job.processed_count} of ${job.total_count} processed (${pct}%)`;

      metricTotal.textContent = job.total_count;
      metricProcessed.textContent = job.processed_count;
      metricSuccess.textContent = job.success_count;
      metricFailed.textContent = job.failed_count;

      if (['COMPLETED', 'PARTIALLY_FAILED', 'FAILED'].includes(job.status)) {
        bannerLiveIndicator.style.display = 'none';
      } else {
        bannerLiveIndicator.style.display = 'inline-block';
      }

      // ZIP downloads
      if (job.success_count > 0) {
        btnDownloadZipPdf.href = `/api/v1/jobs/${job.id}/download-zip?format=pdf`;
        btnDownloadZipPdf.style.display = 'inline-flex';
        btnDownloadZipPng.href = `/api/v1/jobs/${job.id}/download-zip?format=png`;
        btnDownloadZipPng.style.display = 'inline-flex';
      } else {
        btnDownloadZipPdf.style.display = 'none';
        btnDownloadZipPng.style.display = 'none';
      }

      // Render recipients table
      renderRecipientsTable(allRecipientsCache);

      // Return whether finished
      return ['COMPLETED', 'PARTIALLY_FAILED', 'FAILED'].includes(job.status);
    } catch (err) {
      console.error('Error fetching job status:', err);
      return false;
    }
  }

  function getStatusBadgeClass(status) {
    switch (status) {
      case 'COMPLETED': return 'badge-completed';
      case 'PARTIALLY_FAILED': return 'badge-partially';
      case 'FAILED': return 'badge-failed';
      default: return 'badge-pending';
    }
  }

  function renderRecipientsTable(recipients) {
    const activeFilter = document.querySelector('.filter-btn.active').dataset.filter;
    
    // Update counts
    document.getElementById('count-filter-all').textContent = recipients.length;
    document.getElementById('count-filter-success').textContent = recipients.filter(r => r.status === 'SUCCESS').length;
    document.getElementById('count-filter-failed').textContent = recipients.filter(r => r.status === 'FAILED').length;

    const filtered = activeFilter === 'all' 
      ? recipients 
      : recipients.filter(r => r.status === activeFilter);

    if (filtered.length === 0) {
      recipientsTbody.innerHTML = `<tr><td colspan="6" class="text-center py-4">No recipients matching current filter.</td></tr>`;
      return;
    }

    recipientsTbody.innerHTML = filtered.map(r => {
      const isSuccess = r.status === 'SUCCESS';
      const statusBadge = isSuccess 
        ? `<span class="status-badge badge-completed">SUCCESS</span>` 
        : (r.status === 'FAILED' ? `<span class="status-badge badge-failed">FAILED</span>` : `<span class="status-badge badge-pending">PENDING</span>`);

      const errorText = r.error_message 
        ? `<span style="color: var(--danger); font-size: 0.8rem;">⚠ ${escapeHtml(r.error_message)}</span>` 
        : `<span style="color: var(--text-dim);">-</span>`;

      const actions = isSuccess ? `
        <div class="action-btn-group">
          <button class="btn btn-outline btn-sm btn-preview" data-id="${r.id}" data-name="${escapeHtml(r.recipient_name)}">Preview</button>
          <a href="/api/v1/certificates/${r.id}/download?format=pdf" class="btn btn-primary btn-sm" download>PDF</a>
          <a href="/api/v1/certificates/${r.id}/download?format=png" class="btn btn-outline btn-sm" download>PNG</a>
        </div>
      ` : `<span style="color: var(--text-dim); font-size: 0.8rem;">Unavailable</span>`;

      return `
        <tr>
          <td><strong>${escapeHtml(r.recipient_name)}</strong></td>
          <td>${r.recipient_email ? escapeHtml(r.recipient_email) : '<span style="color:var(--text-dim);">-</span>'}</td>
          <td><span class="mono-code">${escapeHtml(r.certificate_code)}</span></td>
          <td>${statusBadge}</td>
          <td>${errorText}</td>
          <td>${actions}</td>
        </tr>
      `;
    }).join('');

    // Attach preview click handlers
    document.querySelectorAll('.btn-preview').forEach(b => {
      b.addEventListener('click', () => {
        openPreviewModal(b.dataset.id, b.dataset.name);
      });
    });
  }

  // Filter button handlers
  document.querySelectorAll('.filter-btn').forEach(fb => {
    fb.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      fb.classList.add('active');
      renderRecipientsTable(allRecipientsCache);
    });
  });

  // Modal handlers
  function openPreviewModal(certId, recipientName) {
    modal.style.display = 'flex';
    document.getElementById('modal-title').textContent = `Certificate Preview - ${recipientName}`;
    modalImg.style.display = 'none';
    modalLoading.style.display = 'inline-block';

    const pngUrl = `/api/v1/certificates/${certId}/view?format=png`;
    modalImg.src = pngUrl;
    modalImg.onload = () => {
      modalLoading.style.display = 'none';
      modalImg.style.display = 'block';
    };

    modalDownloadPdf.href = `/api/v1/certificates/${certId}/download?format=pdf`;
    modalDownloadPng.href = `/api/v1/certificates/${certId}/download?format=png`;
  }

  modalClose.addEventListener('click', () => modal.style.display = 'none');
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.style.display = 'none';
  });

  // Load Job History
  async function loadJobsHistory() {
    try {
      const res = await fetch('/api/v1/jobs?limit=25');
      if (!res.ok) return;
      const jobs = await res.json();

      document.getElementById('active-jobs-count').textContent = jobs.length;

      if (jobs.length === 0) {
        jobsHistoryTbody.innerHTML = `<tr><td colspan="6" class="text-center py-4">No jobs created yet. Submit a generation job above!</td></tr>`;
        return;
      }

      jobsHistoryTbody.innerHTML = jobs.map(j => {
        const zipBtn = j.success_count > 0 
          ? `<a href="/api/v1/jobs/${j.id}/download-zip?format=pdf" class="btn btn-outline btn-sm" download>ZIP</a>` 
          : '';

        return `
          <tr>
            <td>
              <strong>${escapeHtml(j.event_name)}</strong>
              <div style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(j.title)}</div>
            </td>
            <td><span class="mono-code">${j.id.substring(0, 8)}...</span></td>
            <td>${j.issue_date}</td>
            <td><span class="status-badge ${getStatusBadgeClass(j.status)}">${j.status}</span></td>
            <td><strong>${j.success_count}</strong> / ${j.total_count}</td>
            <td>
              <div class="action-btn-group">
                <button class="btn btn-outline btn-sm btn-inspect-job" data-id="${j.id}">View Details</button>
                ${zipBtn}
              </div>
            </td>
          </tr>
        `;
      }).join('');

      document.querySelectorAll('.btn-inspect-job').forEach(b => {
        b.addEventListener('click', () => {
          trackJob(b.dataset.id);
        });
      });

    } catch (err) {
      console.error('Failed to load history:', err);
    }
  }

  btnRefreshJob.addEventListener('click', () => {
    if (currentActiveJobId) fetchAndRenderJob(currentActiveJobId);
  });
  btnRefreshHistory.addEventListener('click', loadJobsHistory);

  // Certificate Verification portal
  btnDoVerify.addEventListener('click', executeVerification);
  verifyInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') executeVerification();
  });

  async function executeVerification() {
    const code = verifyInput.value.trim();
    if (!code) {
      alert('Please enter a certificate code or ID to verify.');
      return;
    }

    try {
      const res = await fetch(`/api/v1/certificates/verify/${encodeURIComponent(code)}`);
      const data = await res.json();

      verifyResultCard.style.display = 'block';

      if (data.valid) {
        verifyBanner.className = 'verify-status-banner banner-valid';
        verifyIcon.textContent = '✓';
        verifyHeading.textContent = 'Authentic Certificate Verified';
        verifySub.textContent = 'This credential was officially issued and verified against our registry.';

        document.getElementById('v-name').textContent = data.recipient_name || '-';
        document.getElementById('v-code').textContent = data.certificate_code || '-';
        document.getElementById('v-event').textContent = data.event_name || '-';
        document.getElementById('v-date').textContent = data.issue_date || '-';
        document.getElementById('v-issuer').textContent = `${data.issuer_name || ''} (${data.issuer_title || ''})`;
        document.getElementById('v-time').textContent = new Date(data.verified_at).toLocaleString();
      } else {
        verifyBanner.className = 'verify-status-banner banner-invalid';
        verifyIcon.textContent = '✕';
        verifyHeading.textContent = 'Certificate Not Found or Invalid';
        verifySub.textContent = 'No active valid certificate matches this identifier.';

        document.getElementById('v-name').textContent = 'N/A';
        document.getElementById('v-code').textContent = code;
        document.getElementById('v-event').textContent = 'N/A';
        document.getElementById('v-date').textContent = 'N/A';
        document.getElementById('v-issuer').textContent = 'N/A';
        document.getElementById('v-time').textContent = new Date().toLocaleString();
      }
    } catch (err) {
      alert('Verification request failed: ' + err.message);
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/[&<>"']/g, function(m) {
      switch (m) {
        case '&': return '&amp;';
        case '<': return '&lt;';
        case '>': return '&gt;';
        case '"': return '&quot;';
        case "'": return '&#039;';
      }
    });
  }

  // Load initial jobs count
  loadJobsHistory();
});
