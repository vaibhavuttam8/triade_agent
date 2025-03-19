import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Container,
  Grid,
  MenuItem,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { PatientInfo } from '../types';

interface PatientInfoFormProps {
  userId: string;
  token: string;
  onComplete: (patientInfo: PatientInfo) => void;
  initialData?: PatientInfo;
}

const PatientInfoForm: React.FC<PatientInfoFormProps> = ({
  userId,
  token,
  onComplete,
  initialData,
}) => {
  const [age, setAge] = useState<number | ''>('');
  const [sex, setSex] = useState<string>('');
  const [condition, setCondition] = useState<string>('');
  const [conditions, setConditions] = useState<string[]>([]);
  const [allergy, setAllergy] = useState<string>('');
  const [allergies, setAllergies] = useState<string[]>([]);
  const [medication, setMedication] = useState<string>('');
  const [medications, setMedications] = useState<string[]>([]);
  const [email, setEmail] = useState<string>('');
  const [phone, setPhone] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Add items to lists
  const addCondition = () => {
    if (condition && !conditions.includes(condition)) {
      setConditions([...conditions, condition]);
      setCondition('');
    }
  };

  const addAllergy = () => {
    if (allergy && !allergies.includes(allergy)) {
      setAllergies([...allergies, allergy]);
      setAllergy('');
    }
  };

  const addMedication = () => {
    if (medication && !medications.includes(medication)) {
      setMedications([...medications, medication]);
      setMedication('');
    }
  };

  // Remove items from lists
  const removeCondition = (itemToRemove: string) => {
    setConditions(conditions.filter(item => item !== itemToRemove));
  };

  const removeAllergy = (itemToRemove: string) => {
    setAllergies(allergies.filter(item => item !== itemToRemove));
  };

  const removeMedication = (itemToRemove: string) => {
    setMedications(medications.filter(item => item !== itemToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const patientInfo: PatientInfo = {
      user_id: userId,
      age: age as number,
      sex,
      previous_conditions: conditions,
      allergies,
      medications,
      contact_info: {
        email,
        phone,
      },
    };

    try {
      const response = await fetch('http://localhost:8000/patient-info', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(patientInfo),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save patient information');
      }

      onComplete(patientInfo);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to save patient information');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        <Typography variant="h5" gutterBottom>
          Patient Information
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Please provide your health information to help us provide better care.
          This information is confidential and will only be used for your healthcare.
        </Typography>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Age"
                type="number"
                fullWidth
                value={age}
                onChange={(e) => setAge(e.target.value === '' ? '' : Number(e.target.value))}
                InputProps={{ inputProps: { min: 0, max: 120 } }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                select
                label="Sex"
                fullWidth
                value={sex}
                onChange={(e) => setSex(e.target.value)}
              >
                <MenuItem value="male">Male</MenuItem>
                <MenuItem value="female">Female</MenuItem>
                <MenuItem value="other">Other</MenuItem>
                <MenuItem value="prefer-not-to-say">Prefer not to say</MenuItem>
              </TextField>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Pre-existing Health Conditions
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TextField
                  label="Add health condition"
                  fullWidth
                  value={condition}
                  onChange={(e) => setCondition(e.target.value)}
                  sx={{ mr: 1 }}
                />
                <Button variant="outlined" onClick={addCondition}>
                  Add
                </Button>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {conditions.map((cond, index) => (
                  <Chip
                    key={index}
                    label={cond}
                    onDelete={() => removeCondition(cond)}
                  />
                ))}
              </Box>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Allergies
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TextField
                  label="Add allergy"
                  fullWidth
                  value={allergy}
                  onChange={(e) => setAllergy(e.target.value)}
                  sx={{ mr: 1 }}
                />
                <Button variant="outlined" onClick={addAllergy}>
                  Add
                </Button>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {allergies.map((item, index) => (
                  <Chip
                    key={index}
                    label={item}
                    onDelete={() => removeAllergy(item)}
                  />
                ))}
              </Box>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Current Medications
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TextField
                  label="Add medication"
                  fullWidth
                  value={medication}
                  onChange={(e) => setMedication(e.target.value)}
                  sx={{ mr: 1 }}
                />
                <Button variant="outlined" onClick={addMedication}>
                  Add
                </Button>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {medications.map((med, index) => (
                  <Chip
                    key={index}
                    label={med}
                    onDelete={() => removeMedication(med)}
                  />
                ))}
              </Box>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                label="Email"
                type="email"
                fullWidth
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Phone"
                fullWidth
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </Grid>

            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                fullWidth
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Save Information'}
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </Container>
  );
};

export default PatientInfoForm; 