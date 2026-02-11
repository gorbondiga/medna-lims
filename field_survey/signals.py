# https://stackoverflow.com/questions/2719038/where-should-signal-handlers-live-in-a-django-project
# https://docs.djangoproject.com/en/3.2/topics/signals/
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from sample_label.models import SampleMaterial
from .models import FieldSample, FilterSample, SubCoreSample


@receiver(pre_delete, sender=FilterSample)
def cascade_delete_field_sample_and_survey(sender, instance, **kwargs):
    """
    Signal to ensure FieldSample and FieldSurvey are deleted when FilterSample is deleted.
    
    Database CASCADE constraints work ONLY in parent→child direction:
    - When FieldSurvey (parent) is deleted → FieldSample (child) is deleted
    - When FieldSample (parent) is deleted → FilterSample (child) is deleted
    - When FieldSurvey (parent) is deleted → EnvMeasure (child) is deleted
    
    But we want child→parent deletion: FilterSample → FieldSample → FieldSurvey → EnvMeasure
    
    This signal manually deletes both FieldSample and FieldSurvey when FilterSample is deleted.
    The FieldSurvey deletion will then CASCADE to EnvMeasure (that one works correctly).
    """
    # Prevent recursion - if FilterSample is already being deleted via CASCADE, skip
    if hasattr(instance, '_cascade_deleting'):
        return
    
    if instance.field_sample:
        try:
            field_sample = FieldSample.objects.get(pk=instance.field_sample.pk)
            # Get the survey before we delete anything
            field_survey = field_sample.survey_global_id
            
            # Mark the FilterSample to prevent recursion when FieldSample deletion cascades back
            instance._cascade_deleting = True
            
            # Delete FieldSample (this will CASCADE delete FilterSample via database,
            # but our flag will prevent the signal from running again)
            if not hasattr(field_sample, '_being_deleted'):
                field_sample._being_deleted = True
                # Temporarily disconnect the signal to prevent recursion
                pre_delete.disconnect(cascade_delete_field_sample_and_survey, sender=FilterSample)
                try:
                    field_sample.delete()
                finally:
                    # Reconnect the signal
                    pre_delete.connect(cascade_delete_field_sample_and_survey, sender=FilterSample)
            
            # Now delete FieldSurvey (this will CASCADE to EnvMeasure via database constraint)
            if field_survey and not hasattr(field_survey, '_being_deleted'):
                # Check if there are other FieldSamples using this survey
                other_samples = FieldSample.objects.filter(
                    survey_global_id=field_survey
                ).exclude(pk=field_sample.pk).exists()
                
                if not other_samples:
                    # No other samples use this survey, safe to delete
                    field_survey._being_deleted = True
                    field_survey.delete()
                    
        except FieldSample.DoesNotExist:
            # FieldSample is already deleted, nothing to do
            pass

