import { useQuery } from '@tanstack/react-query';
import {
  Alert, Chip, CircularProgress, Stack, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Typography, Paper, Button,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import LoginIcon from '@mui/icons-material/Login';
import { listVisits, type Visit } from '../api/client';

/** Icon + label + colour together — status is never colour-only (WCAG 1.4.1). */
function StateChip({ state }: { state: Visit['state'] }) {
  switch (state) {
    case 'APPROVED':
      return <Chip icon={<CheckCircleOutlineIcon />} label="Approved" color="success" size="small" />;
    case 'CHECKED_IN':
      return <Chip icon={<LoginIcon />} label="Checked in" color="primary" size="small" />;
    case 'PENDING_APPROVAL':
      return <Chip icon={<HourglassEmptyIcon />} label="Pending approval" color="warning" size="small" />;
    default:
      return <Chip label={state.replaceAll('_', ' ').toLowerCase()} size="small" />;
  }
}

/** Screen #3 "My visits" — empty / loading / error states per Section 11.2. */
export default function VisitsPage() {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['visits'],
    queryFn: () => listVisits({ sort: '-createdAt' }),
  });

  if (isPending) {
    return (
      <Stack alignItems="center" py={10} role="status" aria-live="polite">
        <CircularProgress aria-label="Loading visits" />
        <Typography mt={4}>Loading visits…</Typography>
      </Stack>
    );
  }

  if (isError) {
    return (
      <Alert
        severity="error"
        action={<Button color="inherit" size="small" onClick={() => refetch()}>Retry</Button>}
      >
        Could not load visits{('title' in (error as object)) ? `: ${(error as { title: string }).title}` : ''}.
      </Alert>
    );
  }

  if (data.data.length === 0) {
    return (
      <Stack alignItems="center" py={10} spacing={4}>
        <Typography variant="h5" component="h1">No visits yet</Typography>
        <Typography color="text.secondary">
          Pre-register a visitor and they will appear here.
        </Typography>
        <Button variant="contained">New visit</Button>
      </Stack>
    );
  }

  return (
    <>
      <Typography variant="h4" component="h1" gutterBottom>
        My visits
      </Typography>
      <TableContainer component={Paper}>
        <Table aria-label="My visits">
          <TableHead>
            <TableRow>
              <TableCell>Visitor</TableCell>
              <TableCell>Company</TableCell>
              <TableCell>Purpose</TableCell>
              <TableCell>Window</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.data.map((visit) => (
              <TableRow key={visit.visitId} hover>
                <TableCell>{visit.visitor.fullName}</TableCell>
                <TableCell>{visit.visitor.company ?? '—'}</TableCell>
                <TableCell>{visit.purpose}</TableCell>
                <TableCell>
                  {new Date(visit.window.startsAt).toLocaleString()} –{' '}
                  {new Date(visit.window.endsAt).toLocaleTimeString()}
                </TableCell>
                <TableCell><StateChip state={visit.state} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
